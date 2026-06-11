from setuptools import setup

setup(
    name='cta_lib',
    version='1.0.3',
    packages=['cta_lib'],
    url='https://gitea.psi.ch/epics_ioc_modules/cta',
    license='',
    author='',
    author_email='',
    description='python library to interact with cta app on IOC',
    long_description='',
    install_requires=['pyepics', 'numpy'],
    entry_points={
        'console_scripts': [
            'cta_lib_ex01_upload_download_print = cta_lib.cta_lib_ex01_upload_download_print:main',
            'cta_lib_ex02_upload_repeat_n_wait = cta_lib.cta_lib_ex02_upload_repeat_n_wait:main',
            'cta_lib_ex03_upload_run_forever_stop = cta_lib.cta_lib_ex03_upload_run_forever_stop:main',
            'cta_lib_ex04_callbacks = cta_lib.cta_lib_ex04_callbacks:main',
        ]
    },
)
