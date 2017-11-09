#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, ConfigureEnvironment, tools
import os


class LibJpegTurboConan(ConanFile):
    name = "libjpeg-turbo"
    version = "1.5.2"
    description = "SIMD-accelerated libjpeg-compatible JPEG codec library"
    generators = "cmake", "txt"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "SSE": [True, False]}
    default_options = "shared=False", "fPIC=True", "SSE=True"
    exports = "CMakeLists.txt"
    url="http://github.com/bincrafters/conan-libjpeg-turbo"
    license="https://github.com/libjpeg-turbo/libjpeg-turbo/blob/%s/LICENSE.txt" % version
    
    def config(self):
        del self.settings.compiler.libcxx 
        
        if self.settings.os == "Windows":
            self.requires.add("nasm/2.12.02@lasote/stable", private=True)
            self.options.remove("fPIC")
       
    def source(self):
        download_url_base = "http://downloads.sourceforge.net/project/libjpeg-turbo"
        archive_prefix = "/" + self.version + "/"
        archive_name = self.name + "-" + self.version
        archive_ext = ".tar.gz"
        download_url =  download_url_base + archive_prefix + archive_name + archive_ext
        self.output.info("trying download of url: " + download_url)
        tools.get(download_url)
        os.rename(archive_name, "sources")

    def build(self):
        with tools.chdir("sources"):
            env = ConfigureEnvironment(self)
            if self.settings.os == "Linux" or self.settings.os == "Macos":
                if self.options.fPIC:
                    env_line = env.command_line.replace('CFLAGS="', 'CFLAGS="-fPIC ')
                else:
                    env_line = env.command_line
                self.run("autoreconf -fiv")
                config_options = ""
                if self.settings.arch == "x86":
                    if self.settings.os == "Linux":
                        config_options = "--host i686-pc-linux-gnu CFLAGS='-O3 -m32' LDFLAGS=-m32"
                    else:
                        config_options = "--host i686-apple-darwin CFLAGS='-O3 -m32' LDFLAGS=-m32"

                if self.settings.os == "Macos":
                    old_str = r'-install_name \$rpath/\$soname'
                    new_str = r'-install_name \$soname'
                    tools.replace_in_file("configure", old_str, new_str)

                self.run("%s ./configure %s" % (env_line, config_options))
                self.run("%s make" % (env_line))
            else:
                # Don't mess with runtime conan already set
                tools.replace_in_file("CMakeLists.txt", 'string(REGEX REPLACE "/MD" "/MT" ${var} "${${var}}")', "")
                tools.replace_in_file("sharedlib/CMakeLists.txt", 'string(REGEX REPLACE "/MT" "/MD" ${var} "${${var}}")', "")
                
                cmake_options = []
                if self.options.shared == True:
                    cmake_options.append("-DENABLE_STATIC=0 -DENABLE_SHARED=1")
                else:
                    cmake_options.append("-DENABLE_SHARED=0 -DENABLE_STATIC=1")
                cmake_options.append("-DWITH_SIMD=%s" % "1" if self.options.SSE else "0")
                
                cmake = CMake(self.settings)
                self.run("mkdir _build" )
                cd_build = "cd _build"

                self.run('%s && %s && cmake .. %s %s' % (env.command_line, cd_build, cmake.command_line, " ".join(cmake_options)))
                self.run("%s && %s && cmake --build . %s" % (env.command_line, cd_build, cmake.build_config))
                
    def package(self):
        # Copying headers
        self.copy("*.h", dst="include", src="sources")
        self.copy(pattern="*.dll", dst="bin", src="sources", keep_path=False)
        self.copy(pattern="*turbojpeg.lib", dst="lib", src="sources", keep_path=False)
        self.copy(pattern="*jpeg.lib", dst="lib", src="sources", keep_path=False)
        self.copy(pattern="*jpeg-static.lib", dst="lib", src="sources", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", src="sources", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", src="sources", keep_path=False)
        self.copy(pattern="*.a", dst="lib", src="sources", keep_path=False)

    def package_info(self):
        if self.settings.os == "Windows":
            if self.options.shared:
                self.cpp_info.libs = ['jpeg', 'turbojpeg']
            else:
                self.cpp_info.libs = ['jpeg-static', 'turbojpeg-static']
        else:
            self.cpp_info.libs = ['jpeg', 'turbojpeg']
