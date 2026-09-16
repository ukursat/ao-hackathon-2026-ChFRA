# Alert Storm Correlator — AO Hackathon 2026

Python 3.11+, NetworkX ve resmi MCP SDK v1. Veritabanı/auth yoktur.
CLI ve MCP aynı `src/analysis.py` motorunu kullanır. `reporter.py` korunmuştur.

## Kurulum ve çalıştırma

- Kurulum: `python -m pip install -r requirements.txt`
- MCP stdio: depo kökünde `python -m src.mcp_server`
- Terminal/HTML/JSON demo: `python -m src.main`
- Test: `python -m unittest discover -s tests -v`

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
