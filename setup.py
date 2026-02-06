from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tf-defect-metrics",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Terraform defect prediction metrics collection tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tf-defect-prediction-github-action",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydriller>=2.0",
        "scikit-learn>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "tf-metrics=scripts.collect_metrics:main",
        ],
    },
    package_data={
        "": ["libs/*.jar"],
    },
    include_package_data=True,
)
