import os
import glob
import sys
import shutil
from setuptools import setup, Extension
from Cython.Build import cythonize

# 获取setup.py所在的目录路径
setup_dir = os.path.dirname(os.path.abspath(__file__))

# 清理src目录中已存在的.cpp文件
src_dir = os.path.join(setup_dir, 'src')
for cpp_file in glob.glob(os.path.join(src_dir, '*.cpp')):
    print(f"删除已存在的C++文件: {cpp_file}")
    os.remove(cpp_file)

# 检测操作系统并配置相应的编译选项
if os.name == 'nt':  # Windows
    libraries = ['user32', 'gdi32', 'psapi']
    extra_compile_args = ['/O2', '/std:c++17']
    extra_link_args = []
else:  # Linux/Mac
    libraries = []
    extra_compile_args = ['-O2', '-std=c++17']
    extra_link_args = []

# 自动发现所有.pyx文件
pyx_files = glob.glob(os.path.join(src_dir, '*.pyx'))

if not pyx_files:
    print("错误: 没有找到任何.pyx文件进行编译")
    sys.exit(1)

print(f"找到 {len(pyx_files)} 个.pyx文件:")
for pyx in pyx_files:
    print(f"  - {pyx}")

extensions = [
    Extension(
        os.path.splitext(os.path.basename(pyx))[0],
        sources=[pyx],
        libraries=libraries,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        language='c++'
    )
    for pyx in pyx_files
]

# 确保build目录存在
build_dir = os.path.join(setup_dir, 'build')
os.makedirs(build_dir, exist_ok=True)

setup(
    name="deltaforce-core",
    version="1.0.0",
    description="DeltaForce Core - Cython扩展模块",
    author="DeltaForce Team",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': "3",
            'embedsignature': True,
            'boundscheck': False,
            'wraparound': False,
            'initializedcheck': False,
            'cdivision': True,
            'nonecheck': False
        },
        build_dir=build_dir  # 明确指定Cython输出目录
    ),
    options={
        'build': {
            'build_base': build_dir
        },
        'build_ext': {
            'build_lib': os.path.join(setup_dir, 'dist'),
            'build_temp': os.path.join(build_dir, 'temp')  # 临时文件目录
        }
    },
    zip_safe=False
)
