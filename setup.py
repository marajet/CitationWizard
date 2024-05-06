from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': [], 'excludes': []}

base = 'gui'

executables = [
    Executable('main.py', base=base, target_name = 'test')
]

setup(name='test',
      version = '1.0',
      description = 'test',
      options = {'build_exe': build_options},
      executables = executables)
