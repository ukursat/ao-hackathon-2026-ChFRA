# Alert Storm Correlator — Kanıtlar

## 1. AI Stratejimiz

LLM, MCP üzerinden deterministik analiz kanıtlarını yorumlar; sunucu LLM
çıktısı taklidi yapmaz. Kararlar tüm kayıtlar üzerinde bellek içinde hesaplanır.

- `src/data_loader.py:81–99`: önce veri sözlüğü; alarm tipi, severity, benzersiz
  ID ve host/servis eşleşmesi doğrulaması; izole servislerin grafa eklenmesi.
- `src/analysis.py:85–104`: servis bazlı zaman oturumları ve aktif A→B grafı.
- `src/analysis.py:106–140`: SCC ile döngü yönetimi, hedef yönünde erişilebilir
  uç bileşenlerin kök adayları olarak seçimi; her alarm için rol ve graf yolu.
- `src/analysis.py:142–161`: aynı kökün yakın oturumlarının birleştirilmesi;
  uzun süreli sinyal kesilmez. 10/30 dakika eşikleri açık heuristiklerdir.

## 2. Çalıştırma ve kapsam

- Kurulum: `python -m pip install -r requirements.txt`
- MCP stdio: `python -m src.mcp_server`
- CLI: `python -m src.main`
- Test: `python -m unittest discover -s tests -v`

MCP araçları `src/mcp_server.py:65`, `:80`, `:99`, `:112` satırlarındadır:
load_and_correlate_alerts, get_noise_audit_log, explain_root_cause,
update_action_status.
Resmi MCP v1 kullanılır; v2 API farklı olduğu için `<2` sınırı uygulanır.

## 3. X-Factor

- `src/analysis.py:26–69`: düşük şiddetli/bakım sinyali ancak ±10 dakikada
  güçlü topolojik kanıt yoksa bastırılır; her alarm için ID ve gerekçe korunur.
- `src/analysis.py:195–217`: tüm ham olay alarmları, envanter, tip/şiddet sayımı,
  servis ilk/son zamanları, aday kökler ve karşı olasılıklar LLM'e sunulur.
- `src/analysis.py:219–226`: en fazla 15 kart, kayıpsız ID muhasebesi ve taşma uyarısı.
- `src/mcp_server.py:80–95`: türev etkiler, bastırılan gerçek gürültü adaylarından
  ayrı denetlenir. Tam audit döndürülür; örnekleme ve sessiz kesme yoktur.
- `src/rca_explanation.py:7`: doğal dil RCA; her alternatif için değerlendirme,
  kanıt ID'leri ve doğrulama adımı. Kanıt yoksa alternatif elenmiş sayılmaz.
- `src/mcp_server.py:112`: canlı durum değişimi, UTC zamanlı geçmiş ve yeniden açma.
- `src/mcp_server.py:33–61`: sıralı olay ID'si yerine aynı kanıt kimliği üzerinden
  yeniden yüklemede aksiyon durumu korunur. Süreç yeniden başlatılırsa sıfırlanır.

## 4. Ölçülen sonuç ve sınırlamalar

Güncel veriyle: 3.000 kayıt, 13 kart, 14 bastırılan gürültü adayı,
2.103 kart içinde korunan türev etki; 2.986 alarm kartlarda, ertelenen alarm yok.
Önceki 2.094 türev kaydı gerçek gürültü eleme başarısı olarak sunulamaz.

Kart üst sınırı 15; hedef bundan çok daha az anlamlı olaydır. Mevcut 13 kart
üst sınıra uygundur fakat daha güçlü indirgeme hedefi henüz sağlanmış sayılmaz.
Bağımsız olayları zorla birleştirmek veya taşanları gizlemek başarı değildir.
14 test geçti; gerçek MCP stdio
üzerinden dört araç, durum geçişleri ve yeniden yüklemede geçmiş kontrol edildi.

Bu sonuç kök neden doğruluğu veya gürültü precision ölçümü değildir; jüri
etiketleri mevcut değildir. Topolojik eşzamanlılık nedenselliği kanıtlamaz.
Geniş bağlı oturumlar bağımsız olayları birleştirebilir; düşük severity filtreleri
yanlış negatif üretebilir. Kalibre edilmiş güven skoru ve SLA iddiası yoktur.
İlk/son alarm gerçek recovery zamanı değildir. Remediation otomatik çalıştırılmaz.
