%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

# distribution specific definitions
%define use_systemd (0%{?fedora} && 0%{?fedora} >= 18) || (0%{?rhel} && 0%{?rhel} >= 7) || (0%{?suse_version} == 1315)

%define nginx_home %{_localstatedir}/cache/nginx
%define nginx_user nginx
%define nginx_group nginx

Summary: NGINX Amplify Agent
Name: nginx-amplify-agent
Version: %{amplify_version}
Release: %{amplify_release}%{?dist}
Vendor: Nginx Software, Inc.
Packager: Nginx Software, Inc. <https://www.nginx.com>
Group: System Environment/Daemons
URL: https://github.com/nginxinc
License: 2-clause BSD-like license


Source0:   nginx-amplify-agent-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%if 0%{?amzn}
Requires: python27
%else
Requires: python >= 2.6
%endif
Requires: initscripts >= 8.36
Requires(post): chkconfig


%description
The NGINX Amplify Agent is a small, Python application that
provides system and NGINX metric collection. It is part of
NGINX Amplify - the monitoring and configuration assistance
service for NGINX.
This package installs and runs NGINX Amplify Agent daemon.
See http://nginx.com/amplify for more information


%prep
%setup -q -n nginx-amplify-agent-%{version}
cp -p %{SOURCE0} .


%build
%{__python} -c 'import setuptools; execfile("setup.py")' build


%pre
# Add the "nginx" user
getent group %{nginx_group} >/dev/null || groupadd -r %{nginx_group}
getent passwd %{nginx_user} >/dev/null || \
    useradd -r -g %{nginx_group} -s /sbin/nologin \
    -d %{nginx_home} -c "nginx user"  %{nginx_user}
exit 0



%install
%define python_libexec /usr/bin/
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}
%{__python} -c 'import setuptools; execfile("setup.py")' install -O1 --skip-build --install-scripts %{python_libexec} --root %{buildroot}
mkdir -p %{buildroot}/var/
mkdir -p %{buildroot}/var/log/
mkdir -p %{buildroot}/var/log/amplify-agent/
mkdir -p %{buildroot}/var/
mkdir -p %{buildroot}/var/run/
mkdir -p %{buildroot}/var/run/amplify-agent/


%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}


%files
%define config_files /etc/amplify-agent/
%defattr(-,root,root,-)
%{python_sitelib}/*
%{python_libexec}/*
%{config_files}/*
%attr(0755,nginx,nginx) %dir /var/log/amplify-agent
%attr(0755,nginx,nginx) %dir /var/run/amplify-agent
/etc/init.d/amplify-agent
/etc/logrotate.d/amplify-agent




%post
if [ $1 -eq 1 ] ; then
%if %{use_systemd}
    /usr/bin/systemctl preset amplify-agent.service >/dev/null 2>&1 ||:
%else
    /sbin/chkconfig --add amplify-agent
%endif
    mkdir -p /var/run/amplify-agent
    touch /var/log/amplify-agent/agent.log
    chown nginx /var/run/amplify-agent /var/log/amplify-agent/agent.log
elif [ $1 -eq 2 ] ; then
    %define agent_conf_file /etc/amplify-agent/agent.conf

    # Check for an older version of the agent running
    if command -V pgrep > /dev/null 2>&1; then
        agent_pid=`pgrep amplify-agent || true`
    else
        agent_pid=`ps aux | grep -i '[a]mplify-agent' | awk '{print $2}'`
    fi

    # stop it
    if [ -n "$agent_pid" ]; then
        service amplify-agent stop > /dev/null 2>&1 < /dev/null
    fi

    if [ -f "%{agent_conf_file}" ]; then
        # Change API URL to 1.3
	    sh -c "sed -i.old 's/api_url.*receiver.*$/api_url = https:\/\/receiver.amplify.nginx.com:443\/1.3/' \
	    %{agent_conf_file}"

	    # Add PHP-FPM to config file
	    if ! grep -i phpfpm "%{agent_conf_file}" > /dev/null 2>&1 ; then
            sh -c "echo >> %{agent_conf_file}" && \
            sh -c "echo '[extensions]' >> %{agent_conf_file}" && \
            sh -c "echo 'phpfpm = True' >> %{agent_conf_file}"
        fi
    else
        test -f "%{agent_conf_file}.default" && \
        cp -p "%{agent_conf_file}.default" "%{agent_conf_file}" && \
        chmod 644 %{agent_conf_file} && \
	    chown nginx %{agent_conf_file} > /dev/null 2>&1
    fi

    # start it
    service amplify-agent start > /dev/null 2>&1 < /dev/null
fi

%preun
if [ $1 -eq 0 ]; then
%if %use_systemd
    /usr/bin/systemctl --no-reload disable amplify-agent.service >/dev/null 2>&1 ||:
    /usr/bin/systemctl stop amplify-agent.service >/dev/null 2>&1 ||:
%else
    /sbin/service amplify-agent stop > /dev/null 2>&1
    /sbin/chkconfig --del amplify-agent
%endif
fi



%changelog
* Tue Oct 18 2017 Grant Hulegaard <grant.hulegaard@nginx.com> 0.47-1
- 0.47-1
- New config parser
- Debug mode
- Bug fix for error logging with PHP-FPM

* Sat Sep 23 2017 Mike Belov <dedm@nginx.com> 0.46-2
- 0.46-2
- Fixes for Centos6

* Thu Sep 21 2017 Grant Hulegaard <grant.hulegaard@nginx.com> 0.46-1
- 0.46-1
- Bug fixes

* Thu Aug 17 2017 Mike Belov <dedm@nginx.com> 0.45-2
- 0.45-2
- Fixes for config parser

* Wed Aug  9 2017 Mike Belov <dedm@nginx.com> 0.45-1
- 0.45-1
- PHP-FPM bug fixes
- Fixes for config parser

* Mon Jun 19 2017 Mike Belov <dedm@nginx.com> 0.44-2
- 0.44-2
- PHP-FPM bug fixes

* Thu Jun 15 2017 Mike Belov <dedm@nginx.com> 0.44-1
- 0.44-1
- PHP-FPM bug fixes

* Thu May 18 2017 Mike Belov <dedm@nginx.com> 0.43-1
- 0.43-1
- PHP-FPM bug fixes
- Memory leak fixes
- Bug fixes

* Mon Apr 17 2017 Mike Belov <dedm@nginx.com> 0.42-2
- 0.42-2
- PHP-FPM bug fixes

* Mon Apr  3 2017 Mike Belov <dedm@nginx.com> 0.42-1
- 0.42-1
- PHP-FPM support
- Tags support
- Memory leak fixes
- Bug fixes

* Thu Jan 19 2017 Mike Belov <dedm@nginx.com> 0.41-2
- 0.41-2
- Updated requests library (fixes some memory leaks)
- Fixes for config and nginx -V parsing

* Thu Jan  5 2017 Mike Belov <dedm@nginx.com> 0.41-1
- 0.41-1
- Generic support for *nix systems
- Fixes for config parser

* Mon Nov  7 2016 Mike Belov <dedm@nginx.com> 0.40-2
- 0.40-2
- Bug fixe8

* Tue Nov  1 2016 Mike Belov <dedm@nginx.com> 0.40-1
- 0.40-1
- Bug fixes
- Syslog support

* Wed Sep 28 2016 Mike Belov <dedm@nginx.com> 0.39-3
- 0.39-3
- Bug fixes

* Wed Sep 21 2016 Mike Belov <dedm@nginx.com> 0.39-2
- 0.39-2
- Bug fixes

* Tue Sep 20 2016 Mike Belov <dedm@nginx.com> 0.39-1
- 0.39-1
- Config parser improvements
- Log parser improvements
- Bug fixes

* Thu Aug 25 2016 Mike Belov <dedm@nginx.com> 0.38-1
- 0.38-1
- FreeBSD support
- Bug fixes

* Thu Jul 28 2016 Mike Belov <dedm@nginx.com> 0.37-1
- 0.37-1
- Bug fixes

* Mon Jul 18 2016 Mike Belov <dedm@nginx.com> 0.36-1
- 0.36-1
- Bug fixes

* Wed Jun 29 2016 Mike Belov <dedm@nginx.com> 0.35-1
- 0.35-1
- New metrics for NGINX+
- Bug fixes

* Wed Jun 22 2016 Mike Belov <dedm@nginx.com> 0.34-2
- 0.34-2
- Bug fixes

* Fri Jun 10 2016 Mike Belov <dedm@nginx.com> 0.34-1
- 0.34-1
- NGINX+ metrics aggregation support
- Bug fixes

* Thu May  5 2016 Mike Belov <dedm@nginx.com> 0.33-3
- 0.33-3
- Bug fixes

* Thu May  5 2016 Mike Belov <dedm@nginx.com> 0.33-2
- 0.33-2
- Bug fixes

* Fri Apr 29 2016 Mike Belov <dedm@nginx.com> 0.33-1
- 0.33-1
- NGINX+ objects support
- Bug fixes

* Wed Apr 13 2016 Mike Belov <dedm@nginx.com> 0.32-1
- 0.32-1
- Bug fixes
- psutil==4.0.0 support

* Thu Mar 31 2016 Mike Belov <dedm@nginx.com> 0.31-1
- 0.31-1
- Bug fixes

* Tue Mar 15 2016 Mike Belov <dedm@nginx.com> 0.30-1
- 0.30-1
- Bug fixes
- Initial SSL analytics support

* Tue Jan 19 2016 Mike Belov <dedm@nginx.com> 0.28-1
- 0.28-1
- Bug fixes
- Amazon Linux support
- Initial NGINX+ extended status support

* Thu Dec 17 2015 Mike Belov <dedm@nginx.com> 0.27-1
- 0.27-1
- Bug fixes

* Thu Dec  3 2015 Mike Belov <dedm@nginx.com> 0.25-1
- 0.25-1
- Bug fixes
- New metric: system.cpu.stolen
- Nginx config parsing improved

* Tue Nov 24 2015 Mike Belov <dedm@nginx.com> 0.24-2
- 0.24-2
- Bug fixes

* Tue Nov 24 2015 Mike Belov <dedm@nginx.com> 0.24-1
- 0.24-1
- Bug fixes

* Wed Nov 18 2015 Mike Belov <dedm@nginx.com> 0.23-1
- 0.23-1
- Bug fixes
- Ubuntu Wily support

* Sun Nov 15 2015 Mike Belov <dedm@nginx.com> 0.22-5
- 0.22-5
- Bug fixes

* Fri Nov 13 2015 Mike Belov <dedm@nginx.com> 0.22-4
- 0.22-4
- Bug fixes

* Thu Nov 12 2015 Mike Belov <dedm@nginx.com> 0.22-3
- 0.22-3
- Bug fixes

* Wed Nov 11 2015 Mike Belov <dedm@nginx.com> 0.22-2
- 0.22-2
- Bug fixes

* Mon Nov  9 2015 Mike Belov <dedm@nginx.com> 0.22-1
- 0.22-1
- Bug fixes

* Thu Nov  5 2015 Mike Belov <dedm@nginx.com> 0.21-3
- 0.21-3
- Additional events added

* Wed Nov  4 2015 Mike Belov <dedm@nginx.com> 0.21-2
- 0.21-2
- Bug fixes

* Mon Nov  2 2015 Mike Belov <dedm@nginx.com> 0.21-1
- 0.21-1
- Bug fixes

* Wed Oct 28 2015 Mike Belov <dedm@nginx.com> 0.20-1
- 0.20-1
- RPM support
