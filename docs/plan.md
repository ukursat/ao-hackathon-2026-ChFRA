# Çözüm Yöntemi ve İyileştirme Planı

## 1. Problem sözleşmesi

3.000 alarmın tümünü incele; aynı olayı tekrar eden veya türev sinyalleri ayrı
müdahale hedefi yapma. En fazla 15 kart göster; sayı değil doğru kök neden ve
kayıpsız açıklanabilirlik önceliklidir. Bağımsız olayları zorla birleştirme.

## 2. Veriyi doğrula

Önce `data/VERI_SOZLUGU.md` okunur. `alarms.json`, bağımlılık CSV'si ve host
envanteri belleğe yüklenir. Zorunlu alanlar, 1–5 tam sayı severity, benzersiz
alarm ID'leri, sözlükteki tipler, host/servis uyumu ve saat dilimi tutarlılığı
denetlenir. `alarms.csv` eşdeğer veri kaynağıdır ancak mevcut yükleyici JSON'u
kullanır. Saat dilimsiz kayıtlara UTC eklenmez.

## 3. Gürültüyü sinyalden ayır

- Güçlü sinyal: severity en az 3 ve bakım alarm tiplerinden biri değil.
- Bakım tipleri: cert_expiry, log_rotate, ntp_drift, backup_warn.
- Zayıf sinyal: severity en fazla 2 veya bakım tipinde severity en fazla 3.
- Zayıf sinyal, ±10 dakikada aynı servis veya bağımlılık zincirinde güçlü
  kanıt bulunmadığında bastırılan gürültü adayıdır.
- Audit; ID, host, zaman, severity, tip, gerekçe, pencere ve kontrol edilen
  servisleri içerir. Bu bir heuristiktir; doğrulanmış gürültü etiketi değildir.

## 4. Topoloji ve zamanla grupla

Servis bazında ardışık sinyaller arasındaki boşluk 10 dakikayı aştığında yeni
oturum açılır. A→B bağımlılık kenarı, iki oturumda ±10 dakika yakın alarm varsa
aktif oturum grafına eklenir. Böylece yalnızca timestamp eşitliğine dayanılmaz.

NetworkX SCC condensation ile döngüler tek bileşene dönüştürülür. Erişilebilir
uç bileşenler kök adaylarıdır. Birden fazla adayda maksimum severity, erken
başlangıç ve ad üzerinden deterministik sıralama yapılır; diğer adaylar RCA
kanıtında korunur. Döngüdeki tek servis kesin kök olarak ilan edilmez.

Aynı kök servis bileşenindeki oturumlar 30 dakika boşluğa kadar birleşir.
Uzun süreli sinyal korunur; bunun gerçekten sızıntı olduğuna karar vermek için
ayrıca metrik trendi gerekir. Bu yöntem normal arka planla köprülenebilir.

## 5. Kayıpsız indirgeme

Kök-bileşen sinyalleri, türev etkiler ve bastırılan gürültü ayrı sınıflardır.
Türev alarmlar kartta korunur, ayrı kart üretilmez. Benzersiz alarm ID'leri
silinerek dedup yapılmaz; tekrarların görünümde gruplanması sağlanır. Tekrarlanan
aynı ID, giriş doğrulama hatasıdır.

Kartlar severity ve alarm sayısıyla sıralanır. Üst sınırın fazlası
`deferred_incidents` içinde uyarıyla korunur, gürültü sayılmaz. Her alarmın
tam bir kez kartlarda veya noise audit içinde olduğu çalışma anında doğrulanır.
Görüntü sınırı nedeniyle kart kesmek, başarılı korelasyon olarak raporlanmaz.

## 6. RCA ve aksiyon

Her kart kök hipotezi, etkilenen/atanan servisler, ham alarm sayısı, ilk/son
zaman ve sahip/durum içeren ilk aksiyon önerisi taşır. `explain_root_cause`
ham metrikler, bağımlılık yolları, kanıt ID'leri ve karşı olasılıkları döndürür.
Alternatif kanıtla elenemiyorsa açıkça elenmedi denir. Sahip ataması servis adı
kurallarıyla önerilir; kurumsal nöbet çizelgesi değildir.

## 7. Doğrulama ve mevcut sonuç

Son ölçüm: 3.000 = 883 kök-bileşen sinyali + 2.103 türev etki + 14 bastırılan
gürültü adayı. 2.986 alarm 13 kartta; ertelenen/kayıp alarm yok. Gürültü adayı
oranı yaklaşık %0,47'dir; %70,10 türev etki oranını gürültü başarısı gibi sunma.

Son test çalışmasında 14 test geçti. Testler tam veri muhasebesi, deterministik
sonuç, graf yönü, döngü, zaman sınırı, kart sınırı, CLI ve gerçek MCP stdio
bağlantısını kapsar. Güncel doğrulama komutu README'dedir.

## 8. Açık işler ve başarı ölçümü

1. Severity ile mesaj semantiğini birlikte incele; sertifika uyarısı veya %26 CPU çöküş kanıtı değildir.
2. İki saate yayılan oturumları baseline ve olay-özgü kanıtlarla yeniden değerlendir.
3. Ağ olaylarında DC/kabin/switch ve paket kaybını karşılaştır; ortak neden kanıtı olmadan birleştirme.
4. Jüri etiketleriyle RCA isabeti, yanlış birleştirme/bölme ve gürültü precision/recall ölç.
5. Recovery, erişilebilirlik SLI ve işlem başarısı olmadan SLA ihlali hesaplama.

`CIKTIRAPORU.txt` mühendis için gözden geçirilmiş kısa rapordur; CLI tarafından
otomatik yenilenmez. Rapor sıralaması motor sıralamasından farklı olabilir;
olay kimliği ve kaynak kanıtı üzerinden izlenebilirlik korunur.
