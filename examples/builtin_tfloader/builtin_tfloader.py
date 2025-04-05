import sys
import os
import tfloader

if __name__ == "__main__":
    try:
        import my_package
    except ImportError as e:
        print(e)
    else:
        print(my_package)
    package_path = os.path.join(sys._stdlib_dir, "package_demo", "my_package.dll")
    print(package_path)
    tfloader.load_tfpackage("my_package", package_path)
    import my_package

    print(my_package)
    print(my_package.add(1, 2))
    from my_package import sub_module

    print(sub_module.substract(4, 2))
    from my_package import sub_package

    sub_package.hello_world()
    from my_package.sub_package import nested_module

    print(nested_module.multiply(3, 44))
