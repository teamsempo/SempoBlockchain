from flask import current_app


def check_mobile_version(version):
    current_mobile_version = current_app.config['MOBILE_VERSION'].split('.')

    # setup latest release - SemVer
    latest_patch = int(current_mobile_version[2])   # fix
    latest_minor = int(current_mobile_version[1])   # feature
    latest_major = int(current_mobile_version[0])   # breaking

    if version:
        # version = '0.0.26'
        v = version.split('.')

        major = int(v[0])
        minor = int(v[1])
        patch = int(v[2])

        if major < latest_major:
            return 'force'

        if minor < latest_minor:
            return 'recommend'

        if patch < latest_patch:
            return 'ok'

        # version is >= latest, return ok
        return 'ok'

    else:
        return
