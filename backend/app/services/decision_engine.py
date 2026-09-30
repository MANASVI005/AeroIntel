CLASS_NAMES = {
    0: "Crack",
    1: "Corrosion",
    2: "Dent",
    3: "Missing Fastener",
}


def calculate_severity(
    class_id: int,
    confidence: float,
    bbox_width: float,
    bbox_height: float,
) -> str:
    """
    Estimate defect severity using model confidence
    and detected bounding-box size.

    This is decision support only.
    It does not replace an engineer's inspection decision.
    """

    area = bbox_width * bbox_height

    # Missing fastener is treated separately because
    # its risk is primarily related to detection confidence.
    if class_id == 3:
        if confidence >= 0.80:
            return "High"
        if confidence >= 0.60:
            return "Medium"
        return "Low"

    # For surface defects, use confidence + relative
    # bounding-box area as an initial screening rule.
    if confidence >= 0.80 and area >= 30000:
        return "High"

    if confidence >= 0.60 and area >= 10000:
        return "Medium"

    if confidence >= 0.80:
        return "Medium"

    return "Low"


def generate_decision_support(
    class_id: int,
    confidence: float,
    bbox_width: float,
    bbox_height: float,
) -> dict:

    class_name = CLASS_NAMES.get(
        class_id,
        f"Unknown ({class_id})",
    )

    severity = calculate_severity(
        class_id=class_id,
        confidence=confidence,
        bbox_width=bbox_width,
        bbox_height=bbox_height,
    )

    progression_status = "New / Baseline"

    if class_id == 0:
        recommended_action = (
            "Perform detailed visual inspection of the detected crack "
            "and compare with previous inspection images when available."
        )

        reasoning = (
            f"Crack detected with {confidence:.1%} confidence. "
            "A baseline inspection is required before progression "
            "can be determined."
        )

    elif class_id == 1:
        recommended_action = (
            "Inspect the corrosion region in detail and compare with "
            "previous inspection images when available."
        )

        reasoning = (
            f"Corrosion detected with {confidence:.1%} confidence. "
            "Corrosion progression cannot be determined from a single "
            "inspection."
        )

    elif class_id == 2:
        recommended_action = (
            "Inspect the dent region and assess its size and condition "
            "against aircraft maintenance requirements."
        )

        reasoning = (
            f"Dent detected with {confidence:.1%} confidence. "
            "A baseline is required to determine whether the defect "
            "has changed over time."
        )

    elif class_id == 3:
        recommended_action = (
            "Inspect the detected fastener location and verify the "
            "fastener condition according to maintenance procedures."
        )

        reasoning = (
            f"Missing fastener detected with {confidence:.1%} confidence. "
            "Physical verification is recommended."
        )

    else:
        recommended_action = (
            "Perform manual inspection of the detected region."
        )

        reasoning = (
            f"Unknown defect class detected with "
            f"{confidence:.1%} confidence."
        )

    return {
        "severity": severity,
        "progression_status": progression_status,
        "recommended_action": recommended_action,
        "reasoning": reasoning,
    }