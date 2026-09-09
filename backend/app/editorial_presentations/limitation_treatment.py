"""Two-state receipt limitation boundary; public copy is authored upstream."""


def public_caveats(treatments, *, source_caveats):
    if not isinstance(treatments, list):
        raise ValueError("limitation treatments must be a list")
    if not isinstance(source_caveats, list) or any(not isinstance(x, str) for x in source_caveats):
        raise ValueError("source caveats must be a string list")
    if [x.get("source_text") if isinstance(x, dict) else None for x in treatments] != source_caveats:
        raise ValueError("limitation treatments must cover each exact source caveat in order")
    result = []
    for entry in treatments:
        if (set(entry) != {"source_text", "treatment", "public_copy"}
                or entry["treatment"] not in {"public", "internal"}
                or not isinstance(entry["public_copy"], str)
                or not entry["source_text"].strip()):
            raise ValueError("invalid governed limitation treatment")
        if entry["treatment"] == "public":
            if not entry["public_copy"].strip():
                raise ValueError("public limitation requires authored public copy")
            result.append(entry["public_copy"])
        elif entry["public_copy"] != "":
            raise ValueError("internal limitation cannot supply public copy")
    return result
