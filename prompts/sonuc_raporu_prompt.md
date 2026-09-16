Çıktı olay kayıtlarını aşağıdaki prompt'a göre işleyip sonuç raporu çıkart. CIKTIRAPORU.txt'yi güncelle. GÖREVLERİN:
 
Gürültüyü Ele (Deduplication): Gelen veri içerisindeki arka plan gürültülerini, tekrar eden kayıtları ve asıl olayın sadece bir "yan etkisi" (symptom) olan ikincil alarmları tamamen yoksay.
Neden-Sonuç İlişkisi Kur (Causality): Olayın başlangıç noktasından (kök neden) sistemin mevcut çöküş anına kadar olan süreci adım adım, mantıksal bir zincir halinde kur.
Karşıt Hipotezleri Çürüt (Counter-Factuals): Mühendisi yanlış yönlendirebilecek alternatif ihtimalleri belirle ve bu ihtimalleri hangi mantıksal/topolojik kanıta dayanarak elediğini açıkla.
Aksiyon Üret (Remediation): Kök nedene yönelik doğrudan çalıştırılabilir bir MCP (Model Context Protocol) aracı ve bu işin sorumlusunu netleştir.
RENKLENDİRME VE GÖRSELLİK KURALLARI (ZORUNLU):
Mühendisin 7 dakika içinde sadece kritik noktalara odaklanabilmesi için çıktı raporunda KESİNLİKLE şu renk/emoji kodlamasını kullanmalısın:
 
🔴 Kırmızı (Kritik): Kök neden ve patlayan ana servisler için.
🟠 Turuncu (Yan Etki): Kök nedenden etkilenip zincirleme çöken servisler için.
🔵 Mavi (Bilgi): Elenen karşı ihtimaller ve çürütme kanıtları için.
🟢 Yeşil (Çözüm): Müdahale aksiyonları ve MCP komutları için.
ÇIKTI FORMATI:
Analiz sonucunu, başka hiçbir giriş veya çıkış cümlesi kullanmadan, SADECE aşağıdaki Markdown şablonunu birebir kullanarak sun. Köşeli parantezli alanları elindeki veriye göre doldur:
 
🔴 [Olayın Kısa Özeti]
🎯 KÖK NEDEN (ROOT CAUSE)
🔴 [Kök Neden Düğümü]: [Durumun Açıklaması]
 
⛓️ NEDEN-SONUÇ ZİNCİRİ (CAUSALITY)
🔴 TETİKLEYİCİ: [Tetikleyen Olay ve Alarm]
🟠 YAN ETKİ: [Topolojide Sıçrama Noktası]
💥 SONUÇ: [Sistemin Mevcut Durumu]
🛡️ ELENEN İHTİMALLER (COUNTER-FACTUALS)
🔵 Elenen İhtimal: [Alternatif Hipotez]
❌ Neden Elendi: [Elenme Kanıtı]
 
🟢 AKSİYON VE ÇÖZÜM (REMEDIATION)
🟢 Aksiyon: [Müdahale Adımı]
👤 Sorumlu Ekip: [İlgili Ekip]
🛠️ MCP Tool: [MCP Komutu veya URI]