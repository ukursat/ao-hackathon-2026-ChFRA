# Proje Aşamaları

## Hedef ve kapsam

Üç saatlik hackathon kapsamında 3.000 alarmı en fazla 15, tercihen çok daha az
anlamlı olay kartına indirmek. Tüm veri bellekte işlenir; DB, auth ve otomatik
üretim müdahalesi kapsam dışıdır. Veri paketi sentetiktir.

## Fazlar ve teslimatlar

| Faz | İş | Teslimat | Durum |
| --- | --- | --- | --- |
| 1 | Veri sözlüğü ve bağımlılık yönünü anlama | Şema, severity 1–5, A→B sözleşmesi | Tamamlandı |
| 2 | Tüm girdileri doğrulayıp belleğe yükleme | `src/data_loader.py` | Tamamlandı |
| 3 | Gürültü ayrımı, zaman oturumları ve graf korelasyonu | `src/analysis.py` | İlk sürüm tamamlandı |
| 4 | Kök hipotezi, karşı olasılık ve ham kanıt sunma | `src/rca_explanation.py` | Tamamlandı |
| 5 | LLM için dört MCP aracı ve durum takibi | `src/mcp_server.py` | Tamamlandı |
| 6 | Terminal, HTML, JSON ve okunabilir inceleme raporu | CLI, `CIKTIRAPORU.txt` | Tamamlandı |
| 7 | Birim, tam veri, CLI ve gerçek MCP/stdio testleri | `tests/test_analysis.py` | Son çalışmada 14 test geçti |
| 8 | Kök neden isabeti ve yanlış birleştirme iyileştirmesi | Etiketli değerlendirme, eşik analizi | Açık |

Bu tablo uygulama durumudur; fazların gerçek çalışma sürelerini ölçmez.

## Üç saatlik demo hazırlık planı

| Önerilen süre | Odak |
| --- | --- |
| 0–20 dakika | Veri, ortam ve giriş doğrulaması |
| 20–80 dakika | Ortak analiz motoru ve alarm muhasebesi |
| 80–120 dakika | RCA açıklamaları ve MCP entegrasyonu |
| 120–150 dakika | Aksiyon yaşam döngüsü ve raporlama |
| 150–180 dakika | Test, demo provası ve jüri belgeleri |

## Kabul durumu

- 3.000 kaydın tamamı hesapta; örnekleme yapılmıyor.
- Son ölçüm 13 kart, 14 bastırılan gürültü adayı ve 2.103 korunan türev etki.
- Her kart kök hipotezi, servisler, alarm sayısı, zaman aralığı ve aksiyon içerir.
- Aksiyon sahibi ve durum kaydı vardır; durum canlı MCP çağrısıyla değiştirilebilir.
- 13 kart üst sınırı karşılar, fakat çok daha az ve yüksek isabetli olay hedefi açık kalır.
- SLA kesinti süresi ve RCA doğruluk oranı için gerekli doğrulama verisi yoktur.

## Demo sırası

1. README kurulumunu tamamlayıp MCP sunucusunu başlat.
2. `load_and_correlate_alerts()` ile tüm veriyi işle ve sayaçları göster.
3. `explain_root_cause(event_id="EVT-005")` ile DB disk kanıtlarını incele.
4. `get_noise_audit_log()` ile bastırılanlar ve türev etkileri ayrı göster.
5. `update_action_status(event_id="EVT-005", new_status="İnceleniyor")` çağır.
6. Kanıt doğrulaması sonrasında demo amaçlı Kapalı/Açık geçişini göster.

EVT kimliklerini her yeniden yüklemede güncel kart listesinden doğrula.
Kapalı durumu servisin gerçekten iyileştiğine dair teknik kanıt değildir.
