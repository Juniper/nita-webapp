%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress

Name:           nita-cmd
Version:        21.7
Release:        1
Summary:        Network Implementation and Test Automation command line interface
Group:          Development/Tools
BuildArch:      noarch
License:        Apache License, Version 2.0, http://www.apache.org/licenses/LICENSE-2.0
URL:            https://www.juniper.net
Source0:        %{name}-%{version}.tar.gz

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description
Command line interface for NITA docker-compose based cli/web application for doing provisioning and testing of network hardware and software

%prep
%setup -q

%build
# Empty section.

%install
rm -rf %{buildroot}
mkdir -p  %{buildroot}
# in builddir
cp -a * %{buildroot}

%clean
rm -rf %{buildroot}

%post
ln -s -f %{_prefix}/local/bin/cli_runner %{_prefix}/local/bin/nita

%preun
rm -f %{_prefix}/local/bin/nita

%files
%defattr(-,root,root,-)
%{_prefix}/local/bin/*
%{_sysconfdir}/bash_completion.d/nita-cmd
%{_sysconfdir}/bash_completion.d/cli_runner_completions

%changelog
* Fri Aug 6 2021 Hugo Ribeiro  21.7-1
  - Release bump
* Thu Nov 26 2020 Ashley Burston 20.10-1
  - Release bump
* Fri Jul 24 2020 Hugo Ribeiro 20.7-1
  - Release bump
* Sat May 2 2020 Ashley Burston 20.4-1
  - Initial rpm release
