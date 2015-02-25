#!/usr/local/bin/perl

#��������������������������������������������������������������������
#�� POST-MAIL : postmail.cgi - 2013/05/30
#�� copyright (c) KentWeb
#�� http://www.kent-web.com/
#��������������������������������������������������������������������

# ���W���[�����s
use strict;
use CGI::Carp qw(fatalsToBrowser);
use lib './lib';
use CGI::Minimal;
use Jcode;
require './lib/base64.pl';

# Jcode�錾
my $j = new Jcode;

# �ݒ�t�@�C���F��
require "./init.cgi";
my %cf = &init;

# �f�[�^��
CGI::Minimal::max_read_size($cf{maxdata});
my $cgi = CGI::Minimal->new;
&error('�e�ʃI�[�o�[') if ($cgi->truncated);
my ($key,$need,$in) = &parse_form;

# �֎~���[�h�`�F�b�N
if ($cf{no_wd}) {
	my $flg;
	foreach (@$key) {
		foreach my $wd ( split(/,/, $cf{no_wd}) ) {
			if (index($$in{$_},$wd) >= 0) {
				$flg++;
				last;
			}
		}
		if ($flg) { &error("�֎~���[�h���܂܂�Ă��܂�"); }
	}
}

# �z�X�g�擾���`�F�b�N
my ($host,$addr) = &get_host;

# �K�{���̓`�F�b�N
my ($check,@err);
if ($$in{need} || @$need > 0) {

	# need�t�B�[���h�̒l��K�{�z��ɉ�����
	my @tmp = split(/\s+/, $$in{need});
	push(@$need,@tmp);

	# �K�{�z��̏d���v�f��r������
	my (@uniq,%seen);
	foreach (@$need) {
		push(@uniq,$_) unless $seen{$_}++;
	}

	# �K�{���ڂ̓��͒l���`�F�b�N����
	foreach (@uniq) {

		# �t�B�[���h�̒l���������Ă��Ȃ����́i���W�I�{�^�����j
		if (!defined($$in{$_})) {
			$check++;
			push(@$key,$_);
			push(@err,$_);

		# ���͂Ȃ��̏ꍇ
		} elsif ($$in{$_} eq "") {
			$check++;
			push(@err,$_);
		}
	}
}

# ���͓��e�}�b�`
my ($match1,$match2);
if ($$in{match}) {
	($match1,$match2) = split(/\s+/, $$in{match}, 2);

	if ($$in{$match1} ne $$in{$match2}) {
		&error("$match1��$match2�̍ē��͓��e���قȂ�܂�");
	}
}

# ���̓`�F�b�N�m�F���
if ($check) {
	&err_check($match2);
}

# --- �v���r���[
if ($$in{mode} ne "send") {

	# �A�����M�`�F�b�N
	&check_post('view');

	# �m�F���
	&preview;

# --- ���M���s
} else {

	# sendmail���M
	&send_mail;
}

#-----------------------------------------------------------
#  �v���r���[
#-----------------------------------------------------------
sub preview {
	# ���M���e�`�F�b�N
	&error("�f�[�^���擾�ł��܂���") if (@$key == 0);

	# ���[�������`�F�b�N
	&check_email($$in{email}) if ($$in{email});

	# ���Ԏ擾
	my $time = time;

	# �Z�b�V��������
	my $ses = &make_ses($time);

	# �e���v���[�g�Ǎ�
	open(IN,"$cf{tmpldir}/conf.html") or &error("open err: conf.html");
	my $tmpl = join('', <IN>);
	close(IN);

	# �e���v���[�g����
	my ($head,$loop,$foot) = $tmpl =~ /(.+)<!-- cell_begin -->(.+)<!-- cell_end -->(.+)/s
			? ($1,$2,$3) : &error("�e���v���[�g���s���ł�");

	# ����
	my $hidden;
	$hidden .= qq|<input type="hidden" name="mode" value="send" />\n|;
	$hidden .= qq|<input type="hidden" name="ses_id" value="$ses" />\n|;

	# ����
	my ($bef,$item);
	foreach my $key (@$key) {
		next if ($bef eq $key);
		next if ($key eq "x");
		next if ($key eq "y");
		next if ($key eq "need");
		next if ($key eq "match");
		next if ($$in{match} && $key eq $match2);
		if ($key eq 'subject') {
			$hidden .= qq|<input type="hidden" name="$key" value="$$in{subject}" />\n|;
			next;
		}

		# name�l�`�F�b�N
		check_key($key) if ($cf{check_key});
		my $val = b64_encode($$in{$key});
		$hidden .= qq|<input type="hidden" name="$key" value="$val" />\n|;

		# ���s�ϊ�
		$$in{$key} =~ s|\t|<br />|g;

		my $tmp = $loop;
		if (defined($cf{replace}->{$key})) {
			$tmp =~ s/!key!/$cf{replace}->{$key}/;
		} else {
			$tmp =~ s/!key!/$key/;
		}
		$tmp =~ s/!val!/$$in{$key}/;
		$item .= $tmp;

		$bef = $key;
	}

	# �����u��
	for ( $head, $foot ) {
		s/!mail_cgi!/$cf{mail_cgi}/g;
		s/<!-- hidden -->/$hidden/g;
	}

	# ��ʓW�J
	print "Content-type: text/html; charset=shift_jis\n\n";
	print $head, $item;

	# �t�b�^�\��
	&footer($foot);
}

#-----------------------------------------------------------
#  ���M���s
#-----------------------------------------------------------
sub send_mail {
	# ���M���e�`�F�b�N
	&error("�f�[�^���擾�ł��܂���") if (@$key == 0);

	# �Z�b�V�����`�F�b�N
	&check_ses;

	# �A�����M�`�F�b�N
	&check_post('send');

	# ���[�������`�F�b�N
	&check_email($$in{email},'send') if ($$in{email});

	# ���Ԏ擾
	my ($date1,$date2) = &get_time;

	# �u���E�U���
	my $agent = $ENV{HTTP_USER_AGENT};
	$agent =~ s/[<>&"'()+;]//g;

	# �{���e���v���ǂݍ���
	my $tbody;
	open(IN,"$cf{tmpldir}/mail.txt") or &error("open err: mail.txt");
	my $tbody = join('', <IN>);
	close(IN);

	# ���s
	$tbody =~ s/\r\n/\n/g;
	$tbody =~ s/\r/\n/g;

	# �e���v���ϐ��ϊ�
	$tbody =~ s/!date!/$date1/g;
	$tbody =~ s/!agent!/$agent/g;
	$tbody =~ s/!host!/$host/g;
	$tbody = $j->set(\$tbody,'sjis')->jis;

	# �����ԐM����̂Ƃ�
	my $resbody;
	if ($cf{auto_res}) {

		# �e���v��
		open(IN,"$cf{tmpldir}/reply.txt") or &error("open err: reply.txt");
		$resbody = join('', <IN>);
		close(IN);

		# ���s
		$resbody =~ s/\r\n/\n/g;
		$resbody =~ s/\r/\n/g;

		# �ϐ��ϊ�
		$resbody =~ s/!date!/$date1/g;
		$resbody = $j->set(\$resbody,'sjis')->jis;
	}

	# �{���L�[��W�J
	my ($bef,$mbody,$log);
	foreach (@$key) {

		# �{���Ɋ܂߂Ȃ�������r��
		next if ($_ eq "mode");
		next if ($_ eq "need");
		next if ($_ eq "match");
		next if ($_ eq "ses_id");
		next if ($_ eq "subject");
		next if ($$in{match} && $_ eq $match2);
		next if ($bef eq $_);

		# B64�f�R�[�h
		$$in{$_} = b64_decode($$in{$_});

		# name�l�̖��O�u��
		my $key_name = defined($cf{replace}->{$_}) ? $cf{replace}->{$_} : $_;

		# �G�X�P�[�v
		$$in{$_} =~ s/\.\n/\. \n/g;

		# �Y�t�t�@�C�����̕����񋑔�
		$$in{$_} =~ s/Content-Disposition:\s*attachment;.*//ig;
		$$in{$_} =~ s/Content-Transfer-Encoding:.*//ig;
		$$in{$_} =~ s/Content-Type:\s*multipart\/mixed;\s*boundary=.*//ig;

		# ���s����
		$$in{$_} =~ s/\t/\n/g;

		# HTML�^�O����
		$$in{$_} =~ s/&lt;/</g;
		$$in{$_} =~ s/&gt;/>/g;
		$$in{$_} =~ s/&quot;/"/g;
		$$in{$_} =~ s/&#39;/'/g;
		$$in{$_} =~ s/&amp;/&/g;

		# �{�����e
		my $tmp;
		if ($$in{$_} =~ /\n/) {
			$tmp = "$key_name = \n$$in{$_}\n";
		} else {
			$tmp = "$key_name = $$in{$_}\n";
		}
		$mbody .= $tmp;

		$bef = $_;
	}
	# �R�[�h�ϊ�
	$mbody = $j->set(\$mbody,'sjis')->jis;

	# �{���e���v�����̕ϐ���u������
	$tbody =~ s/!message!/$mbody/;

	# �ԐM�e���v�����̕ϐ���u������
	$resbody =~ s/!message!/$mbody/ if ($cf{auto_res});

	# ���[���A�h���X���Ȃ��ꍇ�͑��M��ɒu������
	my $email = $$in{email} eq '' ? $cf{mailto} : $$in{email};

	# MIME�G���R�[�h
	my $sub_me = $$in{subject} ne '' && defined($cf{multi_sub}->{$$in{subject}}) ? $cf{multi_sub}->{$$in{subject}} : $cf{subject};
	$sub_me = $j->set($sub_me,'sjis')->mime_encode;
	my $from;
	if ($$in{name}) {
		$$in{name} =~ s/[\r\n]//g;
		$from = $j->set("\"$$in{name}\" <$email>",'sjis')->mime_encode;
	} else {
		$from = $email;
	}

	# --- ���M���e�t�H�[�}�b�g�J�n
	# �w�b�_�[
	my $body = "To: $cf{mailto}\n";
	$body .= "From: $from\n";
	$body .= "Subject: $sub_me\n";
	$body .= "MIME-Version: 1.0\n";
	$body .= "Date: $date2\n";
	$body .= "Content-type: text/plain; charset=iso-2022-jp\n";
	$body .= "Content-Transfer-Encoding: 7bit\n";
	$body .= "X-Mailer: $cf{version}\n\n";
	$body .= "$tbody\n";

	# �ԐM���e�t�H�[�}�b�g
	my $res_body;
	if ($cf{auto_res}) {

		# ����MIME�G���R�[�h
		my $re_sub = Jcode->new($cf{sub_reply},'sjis')->mime_encode;

		$res_body .= "To: $email\n";
		$res_body .= "From: $cf{mailto}\n";
		$res_body .= "Subject: $re_sub\n";
		$res_body .= "MIME-Version: 1.0\n";
		$res_body .= "Content-type: text/plain; charset=iso-2022-jp\n";
		$res_body .= "Content-Transfer-Encoding: 7bit\n";
		$res_body .= "Date: $date2\n";
		$res_body .= "X-Mailer: $cf{version}\n\n";
		$res_body .= "$resbody\n";
	}

	# senmdail�R�}���h
	my $scmd = $cf{send_fcmd} ? "$cf{sendmail} -t -i -f $email" : "$cf{sendmail} -t -i";

	# �{�����M
	open(MAIL,"| $scmd") or &error("���[�����M���s");
	print MAIL "$body\n";
	close(MAIL);

	# �ԐM���M
	if ($cf{auto_res}) {
		my $scmd = $cf{send_fcmd} ? "$cf{sendmail} -t -i -f $cf{mailto}" : "$cf{sendmail} -t -i";

		open(MAIL,"| $scmd") or &error("���[�����M���s");
		print MAIL "$res_body\n";
		close(MAIL);
	}

	# �����[�h
	if ($cf{reload}) {
		if ($ENV{PERLXS} eq "PerlIS") {
			print "HTTP/1.0 302 Temporary Redirection\r\n";
			print "Content-type: text/html\n";
		}
		print "Location: $cf{back}\n\n";
		exit;

	# �������b�Z�[�W
	} else {
		open(IN,"$cf{tmpldir}/thx.html") or &error("open err: thx.html");
		my $tmpl = join('', <IN>);
		close(IN);

		# �\��
		print "Content-type: text/html; charset=shift_jis\n\n";
		$tmpl =~ s/!back!/$cf{back}/g;
		&footer($tmpl);
	}
}

#-----------------------------------------------------------
#  ���̓G���[�\��
#-----------------------------------------------------------
sub err_check {
	my $match2 = shift;

	# �e���v���[�g�ǂݍ���
	my ($err,$flg,$cell,%fname,%err);
	open(IN,"$cf{tmpldir}/err2.html") or &error("open err: err2.html");
	my $tmpl = join('', <IN>);
	close(IN);

	# �e���v���[�g����
	my ($head,$loop,$foot) = $tmpl =~ /(.+)<!-- cell_begin -->(.+)<!-- cell_end -->(.+)/s
			? ($1,$2,$3) : &error("�e���v���[�g���s���ł�");

	# �w�b�_
	print "Content-type: text/html; charset=shift_jis\n\n";
	print $head;

	# ���e�W�J
	my $bef;
	foreach my $key (@$key) {
		next if ($key eq "need");
		next if ($key eq "match");
		next if ($$in{match} && $key eq $match2);
		next if ($bef eq $key);
		next if ($key eq "x");
		next if ($key eq "y");
		next if ($key eq "subject");

		my $key_name = defined($cf{replace}->{$key}) ? $cf{replace}->{$key} : $key;
		my $tmp = $loop;
		$tmp =~ s/!key!/$key_name/;

		my $erflg;
		foreach my $err (@err) {
			if ($err eq $key) {
				$erflg++;
				last;
			}
		}
		# ���͂Ȃ�
		if ($erflg) {
			$tmp =~ s/!val!/<span class="msg">$key_name�͓��͕K�{�ł�.<\/span>/;

		# ����
		} else {
			$$in{$key} =~ s/\t/<br \/>/g;
			$tmp =~ s/!val!/$$in{$key}/;
		}
		print $tmp;

		$bef = $key;
	}

	# �t�b�^
	print $foot;
	exit;
}

#-----------------------------------------------------------
#  �t�H�[���f�R�[�h
#-----------------------------------------------------------
sub parse_form {
	my (@key,@need,%in);
	foreach my $key ( $cgi->param() ) {

		# �����l�̏ꍇ�̓X�y�[�X�ŋ�؂�
		my $val = join(" ", $cgi->param($key));

		# ���Q��/���s�ϊ�
		$key =~ s/[<>&"'\r\n]//g;
		$val =~ s/&/&amp;/g;
		$val =~ s/</&lt;/g;
		$val =~ s/>/&gt;/g;
		$val =~ s/"/&quot;/g;
		$val =~ s/'/&#39;/g;
		$val =~ s/\r\n/\t/g;
		$val =~ s/\r/\t/g;
		$val =~ s/\n/\t/g;

		# �����R�[�h�ϊ�
		if ($cf{conv_code}) {
			$key = $j->set($key)->sjis;
			$val = $j->set($val)->sjis;
		}

		# ���͕K�{
		if ($key =~ /^_(.+)/) {
			$key = $1;
			push(@need,$key);
		}

		# �󂯎��L�[�̏��Ԃ��o���Ă���
		push(@key,$key);

		# %in�n�b�V���ɑ��
		$in{$key} = $val;
	}

	# post���M�`�F�b�N
	if ($cf{postonly} && $ENV{REQUEST_METHOD} ne 'POST') {
		&error("�s���ȃA�N�Z�X�ł�");
	}

	# ���t�@�����X�ŕԂ�
	return (\@key, \@need, \%in);
}

#-----------------------------------------------------------
#  �t�b�^�[
#-----------------------------------------------------------
sub footer {
	my $foot = shift;

	# ���쌠�\�L�i�폜�E���ϋ֎~�j
	my $copy = <<EOM;
<p style="margin-top:2em;text-align:center;font-family:Verdana,Helvetica,Arial;font-size:10px;">
- <a href="http://www.kent-web.com/" target="_top">POST MAIL</a> -
</p>
EOM

	if ($foot =~ /(.+)(<\/body[^>]*>.*)/si) {
		print "$1$copy$2\n";
	} else {
		print "$foot$copy\n";
		print "<body></html>\n";
	}
	exit;
}

#-----------------------------------------------------------
#  �G���[����
#-----------------------------------------------------------
sub error {
	my $err = shift;

	open(IN,"$cf{tmpldir}/err1.html") or &error("open err: err1.html");
	my $tmpl = join('', <IN>);
	close(IN);

	# �����u������
	$tmpl =~ s/!error!/$err/g;

	print "Content-type: text/html; charset=shift_jis\n\n";
	print $tmpl;
	exit;
}

#-----------------------------------------------------------
#  ���Ԏ擾
#-----------------------------------------------------------
sub get_time {
	$ENV{TZ} = "JST-9";
	my ($sec,$min,$hour,$mday,$mon,$year,$wday) = localtime(time);
	my @week  = qw|Sun Mon Tue Wed Thu Fri Sat|;
	my @month = qw|Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec|;

	# �����̃t�H�[�}�b�g
	my $date1 = sprintf("%04d/%02d/%02d(%s) %02d:%02d:%02d",
			$year+1900,$mon+1,$mday,$week[$wday],$hour,$min,$sec);
	my $date2 = sprintf("%s, %02d %s %04d %02d:%02d:%02d",
			$week[$wday],$mday,$month[$mon],$year+1900,$hour,$min,$sec) . " +0900";

	return ($date1,$date2);
}

#-----------------------------------------------------------
#  �z�X�g���擾
#-----------------------------------------------------------
sub get_host {
	# �z�X�g���擾
	my $h = $ENV{REMOTE_HOST};
	my $a = $ENV{REMOTE_ADDR};

	if ($cf{gethostbyaddr} && ($h eq "" || $h eq $a)) {
		$h = gethostbyaddr(pack("C4", split(/\./, $a)), 2);
	}
	if ($h eq "") { $h = $a; }

	# �`�F�b�N
	if ($cf{denyhost}) {
		my $flg;
		foreach ( split(/\s+/, $cf{denyhost}) ) {
			s/\./\\\./g;
			s/\*/\.\*/g;

			if ($h =~ /$_/i) { $flg++; last; }
		}
		if ($flg) { &error("�A�N�Z�X��������Ă��܂���"); }
	}

	return ($h,$a);
}

#-----------------------------------------------------------
#  ���M�`�F�b�N
#-----------------------------------------------------------
sub check_post {
	my $job = shift;

	# ���Ԏ擾
	my $now = time;

	# ���O�I�[�v��
	open(DAT,"+< $cf{logfile}") or &error("open err: $cf{logfile}");
	eval "flock(DAT, 2);";
	my $data = <DAT>;

	# ����
	my ($ip,$time) = split(/<>/, $data);

	# IP�y�ю��Ԃ��`�F�b�N
	if ($ip eq $addr && $now - $time <= $cf{block_post}) {
		close(DAT);
		&error("�A�����M��$cf{block_post}�b�Ԃ��҂���������");
	}

	# ���M���͕ۑ�
	if ($job eq "send") {
		seek(DAT, 0, 0);
		print DAT "$addr<>$now";
		truncate(DAT, tell(DAT));
	}
	close(DAT);
}

#-----------------------------------------------------------
#  �Z�b�V��������
#-----------------------------------------------------------
sub make_ses {
	my $now = shift;

	# �Z�b�V�������s
	my @wd = (0 .. 9, 'a' .. 'z', 'A' .. 'Z', '_');
	my $ses;
	srand;
	for (1 .. 25) {
		$ses .= $wd[int(rand(@wd))];
	}

	# �Z�b�V���������Z�b�g
	my @log;
	open(DAT,"+< $cf{sesfile}") or &error("open err: $cf{sesfile}");
	eval 'floak(DAT, 2);';
	while(<DAT>) {
		chomp;
		my ($id,$time) = split(/\t/);
		next if ($now - $time > $cf{sestime} * 60);

		push(@log,"$_\n");
	}
	unshift(@log,"$ses\t$now\n");
	seek(DAT, 0, 0);
	print DAT @log;
	truncate(DAT, tell(DAT));
	close(DAT);

	return $ses;
}

#-----------------------------------------------------------
#  �Z�b�V�����`�F�b�N
#-----------------------------------------------------------
sub check_ses {
	# �������`�F�b�N
	if ($$in{ses_id} !~ /^\w{25}$/) {
		&error('�s���ȃA�N�Z�X�ł�');
	}

	my $now = time;
	my $flg;
	open(DAT,"$cf{sesfile}") or &error("open err: $cf{sesfile}");
	while(<DAT>) {
		chomp;
		my ($id,$time) = split(/\t/);
		next if ($now - $time > $cf{sestime} * 60);

		if ($id eq $$in{ses_id}) {
			$flg++;
			last;
		}
	}
	close(DAT);

	# �G���[�̂Ƃ�
	if (!$flg) {
		&error('�m�F��ʕ\�����莞�Ԃ��o�߂��܂����B�ŏ������蒼���Ă�������');
	}
}

#-----------------------------------------------------------
#  Base64�G���R�[�h
#-----------------------------------------------------------
sub b64_encode {
	my $data = shift;

	my $str = base64::b64encode($data);
	$str =~ s/\n/\t/g;
	return $str;
}

#-----------------------------------------------------------
#  Base64�f�R�[�h
#-----------------------------------------------------------
sub b64_decode {
	my $str = shift;

	$str =~ s/\t/\n/g;
	return base64::b64decode($str);
}

#-----------------------------------------------------------
#  �d�q���[�������`�F�b�N
#-----------------------------------------------------------
sub check_email {
	my ($eml,$job) = @_;

	# ���M����B64�f�R�[�h
	if ($job eq 'send') { $eml = b64_decode($eml); }

	# E-mail�����`�F�b�N
	if ($eml =~ /\,/) {
		&error("���[���A�h���X�ɃR���} ( , ) ���܂܂�Ă��܂�");
	}
	if ($eml ne '' && $eml !~ /^[\w\.\-]+\@[\w\.\-]+\.[a-zA-Z]{2,6}$/) {
		&error("���[���A�h���X�̏������s���ł�");
	}
}

#-----------------------------------------------------------
#  name�l�`�F�b�N
#-----------------------------------------------------------
sub check_key {
	my $key = shift;

	if ($key !~ /^(?:[0-9a-zA-Z_-]|[\x81-\x9F\xE0-\xFC][\x40-\x7E\x80-\xFC])+$/) {
		error("name�l�ɕs���ȕ������܂܂�Ă��܂�");
	}
}

