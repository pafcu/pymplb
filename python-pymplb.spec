%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           python-pymplb
Version:        0.1
Release:        1%{?dist}
Summary:        Python bindings for MPlayer

Group:          Development/Languages
License:        ISC License
URL:            http://github.com/pafcu/pymplb
Source0:        http://github.com/pafcu/pymplb/tarball/0.1
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python2-devel

%description
pymplb (PYthonMPLayerBingings) is a library that can be used to play media using an external MPlayer process.
The library runs the MPlayer binary in slave mode as a subprocess and then sends slave-mode commands to the process.
Commands are discovered at runtime and thus these bindings should automatically also support any new commands added to MPlayer in the future.

%prep
%setup -q -n pafcu-pymplb-c66cc60

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{python_sitelib}
install -pm 0644 pymplb.py $RPM_BUILD_ROOT%{python_sitelib}
 
%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc README
%{python_sitelib}/*

%changelog
* Mon Oct 11 2010 Stefan Parviainen <pafcu at iki.fi> 0.1
- Initial release
