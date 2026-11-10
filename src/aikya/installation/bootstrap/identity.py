"""Distribution identities shared by installed and standalone bootstraps."""


def package_names(version):
    # Only the inherited v7/v8 series may use the former distribution identity.
    return ('aikya-forge', 'aikya-harness') if version.startswith(('7.', '8.')) else ('aikya-forge',)


def wheel_name(version):
    name = 'aikya_harness' if version.startswith('7.') else 'aikya_forge'
    return name + '-' + version + '-py3-none-any.whl'


def metadata_probe(version):
    """Run inside either generation of payload without importing new helper code."""
    return ('from importlib.metadata import version,PackageNotFoundError\nimport aikya\n'
            'for name in ' + repr(package_names(version)) + ':\n'
            ' try:\n  installed=version(name)\n except PackageNotFoundError:\n  continue\n'
            ' print(installed)\n break\nelse:\n raise RuntimeError("Aikya distribution metadata is missing")\n')
