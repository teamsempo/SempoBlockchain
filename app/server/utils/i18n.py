import i18n


# kwargs are for placeholders
def i18n_for(user, key: str, **kwargs) -> str:
    if user is not None and user.preferred_language is not None:
        i18n.set('locale', user.preferred_language)
    return i18n.t(key, **kwargs)
