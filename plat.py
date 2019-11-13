import distutils.util
print(distutils.util.get_platform().replace('.', '_').replace('-', '_'))
