#!/usr/local/bin/perl

#��������������������������������������������������������������������
#�� POST-MAIL : check.cgi - 2013/05/12
#�� copyright (c) KentWeb
#�� http://www.kent-web.com/
#��������������������������������������������������������������������

# ���W���[���錾
use strict;
use CGI::Carp qw(fatalsToBrowser);

# �O���t�@�C����荞��
require './init.cgi';
my %cf = &init;

print <<EOM;
Content-type: text/html; charset=shift_jis

<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=shift_jis">
<title>Check Mode</title>
</head>
<body>
<b>Check Mode: [ $cf{version} ]</b>
<ul>
<li>Perl�o�[�W���� : $]
EOM

# ���O�t�@�C��
$cf{base64} = './lib/base64.pl';
my %log = (logfile => '���O�t�@�C��', sesfile => '�Z�b�V�����t�@�C��', base64 => 'BASE64���C�u����');
foreach ( keys %log ) {
	if (-f $cf{$_}) {
		print "<li>$log{$_} : OK\n";

		if (-r $cf{$_} && -w $cf{$_}) {
			print "<li>$log{$_} : OK\n";
		} else {
			print "<li>$log{$_} : NG\n";
		}
	} else {
		print "<li>$log{$_} : NG\n";
	}
}

# ���[���\�t�g�`�F�b�N
print "<li>sendmail�p�X : ";
if (-e $cf{sendmail}) {
	print "OK\n";
} else {
	print "NG\n";
}

# �e���v���[�g
my @tmpl = qw|conf.html err1.html err2.html thx.html mail.txt reply.txt|;
foreach (@tmpl) {
	print "<li>�e���v���[�g ( $_ ) : ";

	if (-f "$cf{tmpldir}/$_") {
		print "�p�XOK\n";
	} else {
		print "�p�XNG\n";
	}
}

print <<EOM;
</ul>
</body>
</html>
EOM
exit;

