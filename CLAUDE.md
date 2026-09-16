# AI Yapılandırması ve Kullanım Notu

Projenin VS Code/Copilot yönergeleri `.github/copilot-instructions.md` içindedir.
Bu dosya Claude uyumlu istemciler için aynı proje bağlamına giriş noktasıdır;
Claude modeli kullanıldığı veya bu dosyayla model seçildiği iddiası taşımaz.

## Model kaydı

`ao-hackathon-2026-ChFRA.code-workspace` dosyasında `chat.utilityModel` ve
`chat.utilitySmallModel` değerleri `saka/glm-5.2` olarak yapılandırılmıştır.
Bu ayarlar yardımcı görev tercihleridir; ana sohbet modeli veya gerçek çağrı
logu değildir. Saka, kriz anında kullanılan SRE rolünün adıdır.

## Kullanım şekli

AI asistanı kod, test, dokümantasyon ve kanıt yorumlamada kullanılır.
Sunucu LLM çağırmaz; deterministik NetworkX analizi ve FastMCP araçları sağlar.
İstemci LLM'i load_and_correlate_alerts, get_noise_audit_log ve explain_root_cause
çıktılarından kısa RCA oluşturur; update_action_status yalnızca durum kaydı tutar.
Prompt dosyaları istemci yönergeleridir, otomatik inference yapılandırması değildir.

Tüm veriyi işle, graf yönünü koru, kanıtsız neden/karşı olasılık elemesi üretme.
Proje kuralları için `.github/copilot-instructions.md`, model ve mimari ayrıntıları
için `docs/mimari.md`, yöntem için `docs/plan.md` okunmalıdır.
