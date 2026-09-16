"""Ham kanıttan doğal dil RCA; doğrulanmamış alternatifler elenmiş sayılmaz."""
from __future__ import annotations

from typing import Any


def explain_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    card = metrics["event_card"]
    roots = set(card["root_component_services"])
    alarms = metrics["alarms"]
    root_ids = set(card["root_signal_alarm_ids"])
    evidence = min((a for a in alarms if a["alarm_id"] in root_ids),
                   key=lambda a: (-a["severity"], a["timestamp"], a["alarm_id"]))
    paths: dict[tuple[str, ...], list[str]] = {}
    for assignment in metrics["alarm_assignments"]:
        if assignment["classification"] == "derived_effect":
            paths.setdefault(tuple(assignment["graph_path"]), []).append(assignment["alarm_id"])

    counter_hypotheses = []
    for service in card["impacted_services"]:
        if service in roots:
            continue
        supporting_paths = [list(path) for path in paths if path[0] == service]
        ids = [aid for path, ids in paths.items() if path[0] == service for aid in ids]
        counter_hypotheses.append({
            "hypothesis": f"{service} bağımsız birincil arıza olabilir.",
            "assessment": "daha_az_destekleniyor_elenmedi",
            "reason": f"{service} alarmları aktif bağımlılık yollarıyla kök bileşene "
                      "ulaşıyor; türev etki daha uygun topolojik açıklamadır. "
                      "Bu ilişki bağımsız arızayı kesin olarak elemez.",
            "evidence_alarm_ids": sorted(ids), "graph_paths": supporting_paths,
            "verification_needed": "Dağıtık izlerde bağımlılık hatasını ve bu servisin yerel loglarını karşılaştır.",
        })
    for service in sorted(set(metrics["candidate_root_services"]) - roots):
        counter_hypotheses.append({
            "hypothesis": f"Alternatif aktif kök {service} olabilir.",
            "assessment": "elenmedi",
            "reason": "Bu servis de aktif grafın erişilebilir uç kök adayları arasındadır. "
                      "Seçim şiddet/başlangıç/ad sıralamasıdır; diğer kökü çürüten kanıt değildir.",
            "evidence_alarm_ids": [], "graph_paths": [],
            "verification_needed": f"{service} kök adayına ait olayın ham metriklerini de incele.",
        })
    network_ids = sorted(a["alarm_id"] for a in alarms if a["alarm_type"] in {
        "network_down", "network_flap", "pkt_loss"
    })
    counter_hypotheses.append({
        "hypothesis": "Ortak ağ veya veri merkezi arızası birden çok servisi etkilemiş olabilir.",
        "assessment": "elenmedi",
        "reason": (f"Olayda {len(network_ids)} ağ sinyali var; ortak altyapı alternatifi incelenmeli."
                   if network_ids else "Olayda doğrudan ağ alarmı yok; bu yokluk ağ arızasını dışlamaz."),
        "evidence_alarm_ids": network_ids, "graph_paths": [],
        "verification_needed": "Switch/arayüz metrikleri, paket kaybı ve host/DC dağılımını doğrula.",
    })
    if metrics["cycle_ambiguity"]:
        counter_hypotheses.append({
            "hypothesis": "Döngüdeki başka bir servis asıl tetikleyici olabilir.",
            "assessment": "elenmedi",
            "reason": f"{', '.join(sorted(roots))} aynı güçlü bağlı bileşendedir; "
                      "graf tek bir kökü ayıramaz.",
            "evidence_alarm_ids": sorted(root_ids), "graph_paths": [],
            "verification_needed": "Döngü servislerinin ilk hata anlarını ve trace akışını karşılaştır.",
        })
    explanation = (
        f"Kök neden hipotezi: {card['root_cause_hypothesis']} "
        f"Somut sinyal {evidence['alarm_id']}: {evidence['host']} üzerinde "
        f"{evidence['timestamp']} zamanında {evidence['alarm_type']} "
        f"(severity {evidence['severity']}). "
        f"Topolojik kök bileşeninde {card['alarm_count_root_signal']} alarm, "
        f"bağımlı servislerde {card['alarm_count_derived_effect']} türev etki adayı var. "
        "Kaynak→hedef yolları hedefi kök aday olarak destekler; zaman yakınlığı "
        "ve topoloji tek başına nedensellik kanıtı değildir. "
        + ("Döngü nedeniyle tek servis kesinleştirilemez. " if metrics["cycle_ambiguity"] else "")
        + "Bağımsız servis ve ortak altyapı alternatifleri aşağıdaki kanıtlarla değerlendirilmiştir; "
        "doğrulama olmadan kesin elenme veya sayısal olasılık iddiası yoktur."
    )
    return {
        "event_id": card["event_id"],
        "root_cause_hypothesis": card["root_cause_hypothesis"],
        "explanation": explanation,
        "cause_and_effect_paths": [
            {"dependency_path": list(path), "alarm_ids": sorted(ids),
             "explanation": f"{' → '.join(path)} bağımlılık yolu; arıza etkisi ters yönde yayılabilir."}
            for path, ids in sorted(paths.items())
        ],
        "counter_hypotheses": counter_hypotheses,
        **metrics,
    }