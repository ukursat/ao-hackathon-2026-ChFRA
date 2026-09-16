Sen senior düzeyde bir SRE, Veri Bilimcisi ve AI Sistem Mimarısın. Şu an VS Code ortamımda "AO Hackathon 2026 - Alert Storm Correlator" projesi üzerinde çalışıyoruz. Görevin, LLM'in veri setiyle etkileşime girmesini sağlayacak tam teşekküllü bir Python MCP (Model Context Protocol) sunucusu yazmaktır. 

Veri setinin hiçbir yerinde "sampling" (örnekleme) yapılmayacaktır; 3.000 alarmın tamamı işlenmelidir.

### 1. VERİ KAYNAKLARI VE BAĞLAM (DİZİN: ./data/)
Çalışma dizinimizdeki `data/` klasöründe projeye ait tüm dosyalar bulunmaktadır. Kodları yazarken şu sırayı ve kuralları izlemelisin:
1. İlk olarak `data/VERI_SOZLUGU.md` dosyasının içeriğini baz alarak veri şemalarını, alarm şiddet (severity) ölçeğini ve alarm_type listesini anla.
2. `data/alarms.json` (3.000 kayıt, tamamı işlenecek), `data/service_dependencies.csv` (bağımlılık grafiği için) ve `data/host_inventory.csv` dosyalarını okuyacak modüler fonksiyonlar yaz.

### 2. MCP SUNUCUSU GEREKSİNİMLERİ (src/mcp_server.py)
Bana FastMCP (veya standart mcp SDK) kullanarak bir Python sunucusu yaz. Bu sunucu LLM'in kullanabilmesi için şu araçları (tools) barındırmalıdır:

- Tool 1: `load_and_correlate_alerts()`
  İşlevi: Verilerin tamamını okur. `service_dependencies.csv` verisini bir Graph (ağ) yapısına çevirerek (örn. NetworkX ile) alarmları korele eder. Alakasız gürültüleri eler. 3.000 alarmı maksimum 15 anlamlı "Olay Kartına" (Event Card) indirgeyerek JSON formatında döner.
- Tool 2: `get_noise_audit_log()`
  İşlevi: Hangi alarmların (ID'leri ile) neden gürültü kabul edilip elendiğini açıklayan bir denetim raporu döner. (Bu Jürinin beklediği X-Factor özelliğidir).
- Tool 3: `explain_root_cause(event_id)`
  İşlevi: LLM'in belirli bir olay kartı için kök neden hipotezini, nedenlerini ve etkilenen servisleri SRE bakış açısıyla açıklamasını sağlayacak ham metrikleri döner.

### 3. SRE ALGORİTMA MANTIĞI (ZORUNLU)
- Gruplama sadece zaman damgasına (timestamp) göre yapılmamalıdır. Topolojik bağımlılık çok kritiktir. (Örn: A servisi B'ye bağımlıysa ve ikisi de alarm üretiyorsa, kök neden büyük ihtimalle B'dir).
- Uzun süreye yayılan alarmları (sinsi sızıntılar) tespit edecek bir zaman penceresi mantığı kur.
- Veri tabanı kullanma; tüm okuma, filtreleme ve graph işlemleri in-memory (bellek içi) yapılmalıdır.

### 4. ÇIKTI BEKLENTİSİ
Lütfen lafı uzatmadan sırasıyla şunları sağla:
1. `src/mcp_server.py` dosyasının tam ve çalışır kodu.
2. Bu kodun çalışması için gereken `requirements.txt` içeriği (ör: mcp, networkx, pandas vb.).
3. `AI_JURI.md` dosyasındaki "1. AI Stratejimiz" ve "3. X-Factor" bölümlerine kanıt olarak yazabilmemiz için, koddaki gürültü eleme ve kök neden tespiti algoritmalarının hangi satırlarda olduğunu belirten kısa bir not.

Hazırsan, veri sözlüğüne uygun şekilde kodu üretmeye başla.