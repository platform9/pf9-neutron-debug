%define      product pf9-neutron-debug-app-wrapper

%define      _unpackaged_files_terminate_build 0

Name:        %{product}
Version:     %{_version}
Release:     %{_buildnum}
Summary:     Platform9 Neutron Debug pf9app package

License:     Commercial
URL:         http://www.platform9.com

AutoReqProv: no
Provides:    %{product}
BuildArch:   %{_arch}

%define      privatedir /opt/pf9/www/private
%define      roledir /etc/pf9/resmgr_roles/pf9-neutron-debug/%{version}-%{_buildnum}

%description
Platform9 Neutron Debug pf9app package, built from %{_githash}

%prep

%build

%install

# package in www
install -d %{buildroot}%{privatedir}/
install -p -m 644 *.x86_64.deb %{buildroot}%{privatedir}/
install -p -m 644 *.x86_64.rpm %{buildroot}%{privatedir}/

# role config json in resmgr_roles
install -d %{buildroot}%{roledir}/
install -p -m 644 *role.json %{buildroot}%{roledir}

%clean

%files
%defattr(-,root,root,-)
%{privatedir}
%{roledir}
