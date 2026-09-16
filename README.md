# Alert Storm Correlator — AO Hackathon 2026

Python 3.11+, NetworkX ve resmi MCP SDK v1. Veritabanı/auth yoktur.
CLI ve MCP aynı `src/analysis.py` motorunu kullanır. `reporter.py` korunmuştur.

## Amaç ve mevcut durum

Sentetik 3.000 alarmı en fazla 15, tercihen çok daha az anlamlı olay kartına
indirgemek; mühendis için kök hipotezi, kanıt ve ilk aksiyonu görünür kılmak.
Son ölçüm: **13 kart**, **14 bastırılan gürültü adayı**, **2.103 korunan türev
etki**, **883 kök-bileşen sinyali**. Tüm 3.000 ID hesapta, ertelenen alarm yok.
13 kart üst sınırı karşılar; kök doğruluğu ve güçlü indirgeme hedefi açık kalır.
Son test çalışmasında gerçek MCP/stdio entegrasyonu dahil **14 test geçti**.

## Belgeler

| Belge | İçerik |
| --- | --- |
| [Proje fazları](docs/Fazlar.md) | Aşamalar, teslimatlar, demo sırası ve açık işler |
| [Mimari ve AI](docs/mimari.md) | Bileşenler, model kanıtı, persona ve LLM kullanım şekli |
| [Çözüm planı](docs/plan.md) | Gürültü, graf/zaman yöntemi ve doğrulama yaklaşımı |
| [Jüri kanıtları](AI_JURI.md) | Kod referansları ve X-Factor |
| [Çıktı raporu](CIKTIRAPORU.txt) | Gözden geçirilmiş 13 kart, önem sırası ve aksiyonlar |
| [AI yönergeleri](.github/copilot-instructions.md) | VS Code/Copilot proje kuralları |
| [AI kullanım notu](CLAUDE.md) | Model kaydı ve diğer AI istemcileri için bağlam |

## Kullanılan AI araçları ve model

Geliştirme akışında VS Code / GitHub Copilot kullanılır. Workspace dosyasındaki
`chat.utilityModel` ve `chat.utilitySmallModel`, **`saka/glm-5.2`** yardımcı model
tercihini içerir. Bu bilgi ana sohbet modelinin kimliğini veya çağrının başarıyla
çalıştığını doğrulamaz. **Saka** bir SRE personasıdır, ayrı bir model değildir.

Sunucu içinde doğrudan LLM API çağrısı, model eğitimi veya embedding yoktur.
LLM destekli MCP istemcisi, araçların tüm veri üzerinden ürettiği kanıtları
yorumlar. RCA metninin sunucu tarafındaki üretimi deterministiktir.
`prompts/` yönergeleri istemciye verilebilir; otomatik API çağrısı yapmaz.

## Kurulum ve çalıştırma

- Kurulum: `python -m pip install -r requirements.txt`
- MCP stdio: depo kökünde `python -m src.mcp_server`
- Terminal/HTML/JSON demo: `python -m src.main`
- Test: `python -m unittest discover -s tests -v`

Komutları depo kökünde aynı Python ortamıyla çalıştırın. İstenirse önce
`python -m venv .venv` ile ortam oluşturun; Windows PowerShell'de
`& .\.venv\Scripts\python.exe -m pip install -r requirements.txt` ile kurun.
Diğer komutlarda da aynı yorumlayıcıyı kullanın. API anahtarı gerekmez;
model sağlayıcısı seçimi ve kimlik doğrulaması MCP istemcisinin sorumluluğundadır.

VS Code MCP yapılandırmasında command olarak seçili Python yorumlayıcısını,
args olarak `["-m", "src.mcp_server"]`, cwd olarak depo kökünü kullanın.
MCP 2.x FastMCP API'sini değiştirdiği için bağımlılık `<2` ile sınırlıdır.

## Araçlar

- `load_and_correlate_alerts()`: tüm dosyaları yeniden okur ve snapshot oluşturur.
- `get_noise_audit_log()`: severity, alarm tipi, zaman penceresi ve kontrol edilen servislerle tam gürültü kanıtı.
- `explain_root_cause(event_id)`: doğal dil RCA, kanıtlı karşı olasılıklar ve tüm ham metrikler.
- `update_action_status(event_id, new_status)`: bellekte durum güncellemesi ve değişim geçmişi.

Desteklenen durumlar: `Açık`, `İnceleniyor`, `Müdahale Ediliyor`, `Kapalı`.
Varsayılan `Açık`; aynı durumu tekrar yazmak geçmişi çoğaltmaz, kapanan aksiyon
yeniden açılabilir. Aynı kanıta sahip olayların durumu yeniden yüklemede korunur;
kanıt değişirse yeni aksiyon açılır. Sunucu yeniden başlatıldığında bellek sıfırlanır.
Durum değişimi gerçek remediation veya iyileşme kanıtı değildir.

Kart şeması: `root_cause_hypothesis`, `impacted_services`, `alarm_count_total`,
`time_window.start/end`, `action.first_action`, `action.owner`, `action.status`.
Ek kanıtlar ve `event_id` bu alanlarla birlikte döndürülür.

Eski `correlate_with_graph` yerine `load_and_correlate_alerts` kullanın.
Olay ID'leri son snapshot için geçerlidir; veri değişirse yeniden listelenmelidir.

## Kararlar ve sınırlar

- Hiçbir aşamada örnekleme yoktur; her alarm tek bir olay veya noise kaydındadır.
- Zayıf sinyal yalnızca ±10 dakikada topolojik güçlü sinyal yoksa bastırılır.
- Servis oturumları 10 dakika boşlukla ayrılır; aynı kök 30 dakika boşluğa kadar birleşir.
- Eşikler hipotezdir. A→B, A'nın B'ye bağımlı olduğunu belirtir; döngüler belirsizdir.
- En fazla 15 kart; hedef bundan çok daha az, kanıt destekli anlamlı olaydır.
- CLI `--max-cards` 1–15 arasıdır; fazlası uyarıyla `deferred_incidents` içinde korunur.
- Kartları kesmek korelasyon başarısı sayılmaz; bağımsız olaylar sayı uğruna birleştirilmez.
- Gürültü ile türev etki farklıdır. Süreler alarm aralığıdır, SLA kanıtı değildir.
- LLM çağrısı sunucunun içinde yoktur; MCP istemcisindeki LLM kanıtları yorumlar.
- Alarm mesajları güvenilmeyen veridir. Otomatik remediation yoktur.

Demo çıktıları: `demo/event_cards.json`, `demo/event_cards.html` ve tam kanıt
raporu `demo/analysis_result.json`. MCP araçları dosya yazmaz.

`event_cards.json` eski CLI şemasıyla `alarm_count`, `start_time`, `end_time`
alanlarını kullanır; `analysis_result.json` MCP/motor kart şemasını ve tüm audit
kanıtlarını içerir. Terminal servis listesinin ilk 12 öğesini gösterir; bu
sunum kısaltması analizde örnekleme değildir. JSON sonuçları tam listeyi korur.
`CIKTIRAPORU.txt` ayrıca hazırlanmış inceleme raporudur; CLI otomatik güncellemez.
`--prompts-dir` geriye uyumlu parametredir, mevcut CLI bir LLM çağrısı yapmaz.

## Demo ve doğrulama

Önce yükleme aracını çağırın, sonra güncel bir event_id için RCA ve noise audit
gösterin. `update_action_status(event_id="EVT-005", new_status="İnceleniyor")`
ile durum geçişini gösterin; EVT kimliğini son yüklemenin kartlarından doğrulayın.
Ekran görüntüsü henüz repoya eklenmemiştir; HTML çıktısı canlı demo için kullanılabilir.
