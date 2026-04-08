import secrets
import string
import json


def generate_password(rule_json: str | None = None) -> str:
    """根据规则生成随机密码"""
    defaults = {
        "length": 16,
        "uppercase": True,
        "lowercase": True,
        "digits": True,
        "special": True,
        "prefix": "",
        "suffix": "",
        "exclude_chars": "lI1O0",
    }

    if rule_json:
        try:
            rule = {**defaults, **json.loads(rule_json)}
        except json.JSONDecodeError:
            rule = defaults
    else:
        rule = defaults

    charset = ""
    if rule.get("uppercase"):
        charset += string.ascii_uppercase
    if rule.get("lowercase"):
        charset += string.ascii_lowercase
    if rule.get("digits"):
        charset += string.digits
    if rule.get("special"):
        charset += "!@#$%^&*()-_=+"

    exclude = rule.get("exclude_chars", "")
    charset = "".join(c for c in charset if c not in exclude)

    if not charset:
        charset = string.ascii_letters + string.digits

    prefix = rule.get("prefix", "")
    suffix = rule.get("suffix", "")
    body_length = max(rule.get("length", 16) - len(prefix) - len(suffix), 8)

    required = []
    if rule.get("uppercase"):
        pool = [c for c in string.ascii_uppercase if c not in exclude]
        if pool:
            required.append(secrets.choice(pool))
    if rule.get("lowercase"):
        pool = [c for c in string.ascii_lowercase if c not in exclude]
        if pool:
            required.append(secrets.choice(pool))
    if rule.get("digits"):
        pool = [c for c in string.digits if c not in exclude]
        if pool:
            required.append(secrets.choice(pool))
    if rule.get("special"):
        pool = [c for c in "!@#$%^&*()-_=+" if c not in exclude]
        if pool:
            required.append(secrets.choice(pool))

    remaining = body_length - len(required)
    body_chars = required + [secrets.choice(charset) for _ in range(remaining)]
    secrets.SystemRandom().shuffle(body_chars)

    return prefix + "".join(body_chars) + suffix
