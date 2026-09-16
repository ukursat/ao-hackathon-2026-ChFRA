MCP tool'ları için aşağıdaki kriterleri kullanmanı istiyorum. Buna göre kodları güncellemen gerekiyor.
FastMCP (veya standart mcp SDK) kullanarak şu araçları (tools) barındıran bir sunucu yaz:
- Tool 1: `load_and_correlate_alerts()`
  İşlevi: Alarmları NetworkX kullanarak topolojik bağımlılıklarına göre korele et ve "Olay Kartına" indirebildiğin kadar ( en fazla 15 olmalı) indirge.
  Aşağıdaki formatta çıktı üretmeni istiyorum:
  ZORUNLU ŞEMA (JSON):
  - Kök neden hipotezi
  - Etkilenen servis listesi
  - Alarm sayısı (O olaya ait toplam alarm)
  - Zaman aralığı (Olayın başlangıç ve bitiş zamanı)
  - Önerilen İlk Aksiyon
  - Aksiyon Sahibi ve Aksiyon Durumu (Varsayılan: "Açık")
- Tool 2: `get_noise_audit_log()`
  İşlevi: Hangi alarmların neden gürültü kabul edilip elendiğini kanıtlarıyla açıklayan bir denetim raporu dön.
- Tool 3: `explain_root_cause(event_id)`
  İşlevi: (X-FACTOR) Belirli bir olay kartı için kök neden hipotezinin "neden bu olduğunu" doğal dille açıkla VE "neden başka bir şey olmadığını (Karşı Olasılıklar / Counter Probabilities)" belirterek jüriye SRE derinliğini göster.
- Tool 4: `update_action_status(event_id, new_status)`
  İşlevi: Olay kartındaki aksiyonun durumunu ("Açık", "Kapalı" vb.) güncelle (Demoda canlı gösterim için).