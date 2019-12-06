import i18n


# kwargs are for placeholders
def i18n_for(user, key: str, **kwargs) -> str:
    preferred_language = user.get('preferred_language') if isinstance(user, dict) else user.preferred_language
    if user is not None and preferred_language is not None:
        i18n.set('locale', preferred_language)
    return i18n.t(key, **kwargs)
