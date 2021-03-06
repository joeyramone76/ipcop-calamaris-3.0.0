#!/usr/bin/perl
#
# This code is distributed under the terms of the GPL
#
# (c) 2014 umberto.miceli
#
# $Id: calamaris.cgi,v 3.0.1 2014/04/15 00:00:00 umberto.miceli Exp $
#

# Add entry in menu
# MENUENTRY logs 074 "calamaris proxy reports" "calamaris proxy reports"

use strict;

# enable only the following on debugging purpose
#use warnings;
#use CGI::Carp 'fatalsToBrowser';

use Time::Local;
use IO::Socket;

require '/usr/lib/ipcop/general-functions.pl';
require "/usr/lib/ipcop/lang.pl";
require "/usr/lib/ipcop/header.pl";

my $version = `cat /var/ipcop/proxy/calamaris/version`;
my $updflagfile = "/var/ipcop/proxy/calamaris/.up2date";

my $unique=time;

my $squidlogdir = "/var/log/squid";
my $reportdir = "/var/ipcop/proxy/calamaris/reports";

unless (-e $reportdir) { mkdir($reportdir) }

my %cgiparams=();
my %reportsettings=();
my %selected=();
my %checked=();

my $errormessage='';

my $hintcolour='#FFFFCC';

my $commandline='';

my %monthidx = (qw(Jan 0 Feb 1 Mar 2 Apr 3 May 4 Jun 5 Jul 6 Aug 7 Sep 8 Oct 9 Nov 10 Dec 11)); 

my @longmonths = ( $Lang::tr{'january'}, $Lang::tr{'february'}, $Lang::tr{'march'},
	$Lang::tr{'april'}, $Lang::tr{'may'}, $Lang::tr{'june'}, $Lang::tr{'july'},
	$Lang::tr{'august'}, $Lang::tr{'september'}, $Lang::tr{'october'},
	$Lang::tr{'november'}, $Lang::tr{'december'} );

my @now = localtime(time);
my $year = $now[5]+1900;

my $day_begin=0;
my $month_begin=0;
my $year_begin=0;
my $day_end=0;
my $month_end=0;
my $year_end=0;

my $latest=substr(&check4updates,0,length($version));

$reportsettings{'ACTION'} = '';

$reportsettings{'DAY_BEGIN'}   = $now[3];
$reportsettings{'MONTH_BEGIN'} = $now[4];
$reportsettings{'YEAR_BEGIN'}  = $now[5]+1900;
$reportsettings{'DAY_END'}     = $now[3];
$reportsettings{'MONTH_END'}   = $now[4];
$reportsettings{'YEAR_END'}    = $now[5]+1900;

$reportsettings{'ENABLE_DOMAIN'} = 'off';
$reportsettings{'NUM_DOMAINS'} = '10';
$reportsettings{'ENABLE_PERFORMANCE'} = 'off';
$reportsettings{'PERF_INTERVAL'} = '60';
$reportsettings{'ENABLE_CONTENT'} = 'off';
$reportsettings{'NUM_CONTENT'} = '10';
$reportsettings{'ENABLE_REQUESTER'} = 'off';
$reportsettings{'ENABLE_USERNAME'} = 'off';
$reportsettings{'NUM_HOSTS'} = '10';
$reportsettings{'NUM_URLS'} = '0';
$reportsettings{'ENABLE_HISTOGRAM'} = 'off';
$reportsettings{'HIST_LEVEL'} = '10';
$reportsettings{'ENABLE_VERBOSE'} = 'off';
$reportsettings{'BYTE_UNIT'} = 'B';
$reportsettings{'SKIP_GZLOGS'} = 'off';
$reportsettings{'RUN_BACKGROUND'} = 'off';

&General::getcgihash(\%reportsettings);

my $reportfile=$reportsettings{'REPORT'};

if ($reportsettings{'ACTION'} eq $Lang::tr{'calamaris create report'})
{
	$cgiparams{'DAY_BEGIN'}   = $reportsettings{'DAY_BEGIN'};
	$cgiparams{'MONTH_BEGIN'} = $reportsettings{'MONTH_BEGIN'};
	$cgiparams{'YEAR_BEGIN'}  = $reportsettings{'YEAR_BEGIN'};
	$cgiparams{'DAY_END'}     = $reportsettings{'DAY_END'};
	$cgiparams{'MONTH_END'}   = $reportsettings{'MONTH_END'};
	$cgiparams{'YEAR_END'}    = $reportsettings{'YEAR_END'};

	delete $reportsettings{'DAY_BEGIN'};
	delete $reportsettings{'MONTH_BEGIN'};
	delete $reportsettings{'YEAR_BEGIN'};
	delete $reportsettings{'DAY_END'};
	delete $reportsettings{'MONTH_END'};
	delete $reportsettings{'YEAR_END'};
	delete $reportsettings{'REPORT'};

	&General::writehash("/var/ipcop/proxy/calamaris/settings", \%reportsettings);

	$reportsettings{'DAY_BEGIN'}   = $cgiparams{'DAY_BEGIN'};
	$reportsettings{'MONTH_BEGIN'} = $cgiparams{'MONTH_BEGIN'};
	$reportsettings{'YEAR_BEGIN'}  = $cgiparams{'YEAR_BEGIN'};
	$reportsettings{'DAY_END'}     = $cgiparams{'DAY_END'};
	$reportsettings{'MONTH_END'}   = $cgiparams{'MONTH_END'};
	$reportsettings{'YEAR_END'}    = $cgiparams{'YEAR_END'};
	$reportsettings{'REPORT'}      = $cgiparams{'REPORT'};

	$day_begin   = $reportsettings{'DAY_BEGIN'};
	$month_begin = $reportsettings{'MONTH_BEGIN'};
	$year_begin  = $reportsettings{'YEAR_BEGIN'};
	$day_end     = $reportsettings{'DAY_END'};
	$month_end   = $reportsettings{'MONTH_END'};
	$year_end    = $reportsettings{'YEAR_END'};

	if ($reportsettings{'SKIP_GZLOGS'} eq 'on') { $commandline.='nogz '; }

	$commandline.="$day_begin $month_begin $year_begin $day_end $month_end $year_end";

	if ($reportsettings{'ENABLE_DOMAIN'} eq 'on')
	{
		$commandline.=' -d ';
		$commandline.=$reportsettings{'NUM_DOMAINS'};
	}
	if ($reportsettings{'ENABLE_PERFORMANCE'} eq 'on')
	{
		$commandline.=' -P ';
		$commandline.=$reportsettings{'PERF_INTERVAL'};
	}
	if ($reportsettings{'ENABLE_CONTENT'} eq 'on')
	{
		$commandline.=' -t ';
		$commandline.=$reportsettings{'NUM_CONTENT'};
	}
	if ($reportsettings{'ENABLE_HISTOGRAM'} eq 'on')
	{
		$commandline.=' -D ';
		$commandline.=$reportsettings{'HIST_LEVEL'};
	}
	if ($reportsettings{'ENABLE_REQUESTER'} eq 'on')
	{
		if ($reportsettings{'ENABLE_USERNAME'} eq 'on')
		{
			$commandline.=' -u';
		}
		$commandline.=' -r ';
		$commandline.=$reportsettings{'NUM_HOSTS'};

		unless ($reportsettings{'NUM_URLS'} eq '0')
		{
			$commandline.=' -R ';
			$commandline.=$reportsettings{'NUM_URLS'};
		}
	}
	unless ($reportsettings{'BYTE_UNIT'} eq 'B')
	{
		$commandline.=' -U ';
		$commandline.=$reportsettings{'BYTE_UNIT'};
	}
	if ($reportsettings{'ENABLE_VERBOSE'} eq 'on')
	{
		$commandline.=' -s';
	}

	$commandline.=' < /dev/null > /dev/null 2>&1';

	if ($reportsettings{'RUN_BACKGROUND'} eq 'on') { $commandline.=" &"; }

	system("/var/ipcop/proxy/calamaris/bin/mkreport $commandline")
}

if ($reportsettings{'ACTION'} eq $Lang::tr{'export'})
{
	print "Content-type: application/octet-stream\n";
	print "Content-length: ";
	print (-s "$reportdir/$reportsettings{'REPORT'}");
	print "\n";
	print "Content-disposition: attachment; filename=$reportsettings{'REPORT'}\n\n";

	open (FILE, "$reportdir/$reportsettings{'REPORT'}");
	while (<FILE>) { print; }
	close (FILE);

	exit;
}

if ($reportsettings{'ACTION'} eq $Lang::tr{'delete'}) {	unlink("$reportdir/$reportsettings{'REPORT'}"); }

if (-e "/var/ipcop/proxy/calamaris/settings")
{
	&General::readhash("/var/ipcop/proxy/calamaris/settings", \%reportsettings);
}

&Header::showhttpheaders();

$checked{'ENABLE_DOMAIN'}{'off'} = '';
$checked{'ENABLE_DOMAIN'}{'on'} = '';
$checked{'ENABLE_DOMAIN'}{$reportsettings{'ENABLE_DOMAIN'}} = "checked='checked'";
$selected{'NUM_DOMAINS'}{$reportsettings{'NUM_DOMAINS'}} = "selected='selected'";
$checked{'ENABLE_PERFORMANCE'}{'off'} = '';
$checked{'ENABLE_PERFORMANCE'}{'on'} = '';
$checked{'ENABLE_PERFORMANCE'}{$reportsettings{'ENABLE_PERFORMANCE'}} = "checked='checked'";
$selected{'PERF_INTERVAL'}{$reportsettings{'PERF_INTERVAL'}} = "selected='selected'";
$checked{'ENABLE_CONTENT'}{'off'} = '';
$checked{'ENABLE_CONTENT'}{'on'} = '';
$checked{'ENABLE_CONTENT'}{$reportsettings{'ENABLE_CONTENT'}} = "checked='checked'";
$selected{'NUM_CONTENT'}{$reportsettings{'NUM_CONTENT'}} = "selected='selected'";
$checked{'ENABLE_REQUESTER'}{'off'} = '';
$checked{'ENABLE_REQUESTER'}{'on'} = '';
$checked{'ENABLE_REQUESTER'}{$reportsettings{'ENABLE_REQUESTER'}} = "checked='checked'";
$checked{'ENABLE_USERNAME'}{'off'} = '';
$checked{'ENABLE_USERNAME'}{'on'} = '';
$checked{'ENABLE_USERNAME'}{$reportsettings{'ENABLE_USERNAME'}} = "checked='checked'";
$selected{'NUM_HOSTS'}{$reportsettings{'NUM_HOSTS'}} = "selected='selected'";
$selected{'NUM_URLS'}{$reportsettings{'NUM_URLS'}} = "selected='selected'";
$checked{'ENABLE_HISTOGRAM'}{'off'} = '';
$checked{'ENABLE_HISTOGRAM'}{'on'} = '';
$checked{'ENABLE_HISTOGRAM'}{$reportsettings{'ENABLE_HISTOGRAM'}} = "checked='checked'";
$selected{'HIST_LEVEL'}{$reportsettings{'HIST_LEVEL'}} = "selected='selected'";
$checked{'ENABLE_VERBOSE'}{'off'} = '';
$checked{'ENABLE_VERBOSE'}{'on'} = '';
$checked{'ENABLE_VERBOSE'}{$reportsettings{'ENABLE_VERBOSE'}} = "checked='checked'";
$selected{'BYTE_UNIT'}{$reportsettings{'BYTE_UNIT'}} = "selected='selected'";
$checked{'SKIP_GZLOGS'}{'off'} = '';
$checked{'SKIP_GZLOGS'}{'on'} = '';
$checked{'SKIP_GZLOGS'}{$reportsettings{'SKIP_GZLOGS'}} = "checked='checked'";
$checked{'RUN_BACKGROUND'}{'off'} = '';
$checked{'RUN_BACKGROUND'}{'on'} = '';
$checked{'RUN_BACKGROUND'}{$reportsettings{'RUN_BACKGROUND'}} = "checked='checked'";

&Header::openpage($Lang::tr{'calamaris proxy reports'}, 1, '');

&Header::openbigbox('100%', 'left', '', $errormessage);

if ($errormessage) {
	&Header::openbox('100%', 'left', $Lang::tr{'error messages'});
	print "<font class='base'>$errormessage&nbsp;</font>\n";
	&Header::closebox();
}

if (($version lt $latest) && (-e $updflagfile)) { unlink($updflagfile); }

if (!-e $updflagfile) {
	&Header::openbox('100%', 'left', $Lang::tr{'calamaris update notification'});
	print "<table width='100%' cellpadding='5'>\n";
	print "<tr>\n";
	print "<td bgcolor='$hintcolour' class='base'>$Lang::tr{'calamaris update information'}</td>";
	print "</tr>\n";
	print "</table>\n";
	&Header::closebox();
}

&Header::openbox('100%', 'left', "$Lang::tr{'settings'}:");

print <<END
<form method='post' action='$ENV{'SCRIPT_NAME'}'>
<table width='100%' border='0'>
<tr>
	<td colspan='8' class='base'><b>$Lang::tr{'calamaris report period'}</b></td>
</tr>
<tr>
	<td width='9%' class='base'>$Lang::tr{'from'}:</td>
	<td width='15%'>
	<select name='MONTH_BEGIN'>
END
;
for ($month_begin = 0; $month_begin < 12; $month_begin++)
{
	print "\t<option ";
	if ($month_begin == $reportsettings{'MONTH_BEGIN'}) {
		print 'selected="selected" '; }
	print "value='$month_begin'>$longmonths[$month_begin]</option>\n";
}
print <<END
	</select>
	</td>
	<td width='9%'>
	<select name='DAY_BEGIN'>
END
;
for ($day_begin = 1; $day_begin <= 31; $day_begin++) 
{
	print "\t<option ";
	if ($day_begin == $reportsettings{'DAY_BEGIN'}) {
		print 'selected="selected" '; }
	print "value='$day_begin'>$day_begin</option>\n";
}
print <<END
	</select>
	</td>
	<td width='12%'>
	<select name='YEAR_BEGIN'>
END
;
for ($year_begin = $year-2; $year_begin <= $year+1; $year_begin++) 
{
	print "\t<option ";
	if ($year_begin == $reportsettings{'YEAR_BEGIN'}) {
		print 'selected="selected" '; }
	print "value='$year_begin'>$year_begin</option>\n";
}
print <<END
	</select>
	</td>
	<td width='9%' class='base'>$Lang::tr{'to'}:</td>
	<td width='15%'>
	<select name='MONTH_END'>
END
;
for ($month_end = 0; $month_end < 12; $month_end++)
{
	print "\t<option ";
	if ($month_end == $reportsettings{'MONTH_END'}) {
		print 'selected="selected" '; }
	print "value='$month_end'>$longmonths[$month_end]</option>\n";
}
print <<END
	</select>
	</td>
	<td width='9%'>
	<select name='DAY_END'>
END
;
for ($day_end = 1; $day_end <= 31; $day_end++) 
{
	print "\t<option ";
	if ($day_end == $reportsettings{'DAY_END'}) {
		print 'selected="selected" '; }
	print "value='$day_end'>$day_end</option>\n";
}
print <<END
	</select>
	</td>
	<td width='22%'>
	<select name='YEAR_END'>
END
;
for ($year_end = $year-2; $year_end <= $year+1; $year_end++) 
{
	print "\t<option ";
	if ($year_end == $reportsettings{'YEAR_END'}) {
		print 'selected="selected" '; }
	print "value='$year_end'>$year_end</option>\n";
}
print <<END
	</select>
	</td>
</tr>
</table>

<hr size='1'>

<table width='100%' border='0'>
<tr>
	<td colspan='4' class='base'><b>$Lang::tr{'calamaris report options'}</b></td>
</tr>
<tr>
	<td width='30%' class='base'>$Lang::tr{'calamaris enable domain report'}:</td>
	<td width='15%'><input type='checkbox' name='ENABLE_DOMAIN' $checked{'ENABLE_DOMAIN'}{'on'} /> [-d]</td>
	<td width='30%' class='base'>$Lang::tr{'calamaris number of domains'}:</td>
	<td width='25%'><select name='NUM_DOMAINS'>
		<option value='10'  $selected{'NUM_DOMAINS'}{'10'}>10</option>
		<option value='25'  $selected{'NUM_DOMAINS'}{'25'}>25</option>
		<option value='100' $selected{'NUM_DOMAINS'}{'100'}>100</option>
		<option value='-1'  $selected{'NUM_DOMAINS'}{'-1'}>$Lang::tr{'calamaris unlimited'}</option>
	</select></td>
</tr>
<tr>
	<td class='base'>$Lang::tr{'calamaris enable performance report'}:</td>
	<td><input type='checkbox' name='ENABLE_PERFORMANCE' $checked{'ENABLE_PERFORMANCE'}{'on'} /> [-P]</td>
	<td class='base'>$Lang::tr{'calamaris report interval (in minutes)'}:</td>
	<td><select name='PERF_INTERVAL'>
		<option value='30'   $selected{'PERF_INTERVAL'}{'30'}>30</option>
		<option value='60'   $selected{'PERF_INTERVAL'}{'60'}>60</option>
		<option value='120'  $selected{'PERF_INTERVAL'}{'120'}>120</option>
		<option value='240'  $selected{'PERF_INTERVAL'}{'240'}>240</option>
		<option value='480'  $selected{'PERF_INTERVAL'}{'480'}>480</option>
		<option value='720'  $selected{'PERF_INTERVAL'}{'720'}>720</option>
		<option value='1440' $selected{'PERF_INTERVAL'}{'1440'}>1440</option>
	</select></td>
</tr>
<tr>
	<td class='base'>$Lang::tr{'calamaris enable content report'}:</td>
	<td><input type='checkbox' name='ENABLE_CONTENT' $checked{'ENABLE_CONTENT'}{'on'} /> [-t]</td>
	<td class='base'>$Lang::tr{'calamaris number of content types'}:</td>
	<td><select name='NUM_CONTENT'>
		<option value='10'  $selected{'NUM_CONTENT'}{'10'}>10</option>
		<option value='25'  $selected{'NUM_CONTENT'}{'25'}>25</option>
		<option value='100' $selected{'NUM_CONTENT'}{'100'}>100</option>
		<option value='-1'  $selected{'NUM_CONTENT'}{'-1'}>$Lang::tr{'calamaris unlimited'}</option>
	</select></td>
</tr>
<tr>
	<td class='base'>$Lang::tr{'calamaris enable requester report'}:</td>
	<td><input type='checkbox' name='ENABLE_REQUESTER' $checked{'ENABLE_REQUESTER'}{'on'} /> [-r/-R]</td>
	<td class='base'>$Lang::tr{'calamaris number of requesting hosts'}:</td>
	<td><select name='NUM_HOSTS'>
		<option value='10'  $selected{'NUM_HOSTS'}{'10'}>10</option>
		<option value='25'  $selected{'NUM_HOSTS'}{'25'}>25</option>
		<option value='100' $selected{'NUM_HOSTS'}{'100'}>100</option>
		<option value='-1'  $selected{'NUM_HOSTS'}{'-1'}>$Lang::tr{'calamaris unlimited'}</option>
</tr>
<tr>
	<td class='base'>$Lang::tr{'calamaris show usernames'}:</td>
	<td><input type='checkbox' name='ENABLE_USERNAME' $checked{'ENABLE_USERNAME'}{'on'} /> [-u]</td>
	<td class='base'>$Lang::tr{'calamaris number of requested urls'}:</td>
	<td><select name='NUM_URLS'>
		<option value='0'   $selected{'NUM_URLS'}{'0'}>$Lang::tr{'calamaris none'}</option>
		<option value='10'  $selected{'NUM_URLS'}{'10'}>10</option>
		<option value='25'  $selected{'NUM_URLS'}{'25'}>25</option>
		<option value='100' $selected{'NUM_URLS'}{'100'}>100</option>
		<option value='-1'  $selected{'NUM_URLS'}{'-1'}>$Lang::tr{'calamaris unlimited'}</option>
	</select></td>
</tr>
<tr>
	<td class='base'>$Lang::tr{'calamaris enable distribution histogram'}:</td>
	<td><input type='checkbox' name='ENABLE_HISTOGRAM' $checked{'ENABLE_HISTOGRAM'}{'on'} /> [-D]</td>
	<td class='base'>$Lang::tr{'calamaris histogram resolution'}:</td>
	<td><select name='HIST_LEVEL'>
		<option value='1000' $selected{'HIST_LEVEL'}{'1000'}>$Lang::tr{'calamaris low'}</option>
		<option value='10'   $selected{'HIST_LEVEL'}{'10'}>$Lang::tr{'calamaris medium'}</option>
		<option value='2'    $selected{'HIST_LEVEL'}{'2'}>$Lang::tr{'calamaris high'}</option>
</tr>
<tr>
	<td class='base'>$Lang::tr{'calamaris enable verbose reporting'}:</td>
	<td><input type='checkbox' name='ENABLE_VERBOSE' $checked{'ENABLE_VERBOSE'}{'on'} /> [-s]</td>
	<td class='base'>$Lang::tr{'calamaris byte unit'}:</td>
	<td><select name='BYTE_UNIT'>
		<option value='B' $selected{'BYTE_UNIT'}{'B'}>Byte</option>
		<option value='K' $selected{'BYTE_UNIT'}{'K'}>KByte</option>
		<option value='M' $selected{'BYTE_UNIT'}{'M'}>MByte</option>
		<option value='G' $selected{'BYTE_UNIT'}{'G'}>GByte</option>
</tr>
</table>

<hr size='1'>

<table width='100%' border='0'>
<tr>
	<td colspan='4' class='base'><b>$Lang::tr{'calamaris performance options'}</b></td>
</tr>
<tr>
	<td width='30%' class='base'>$Lang::tr{'calamaris skip archived logfiles'}:</td>
	<td width='15%'><input type='checkbox' name='SKIP_GZLOGS' $checked{'SKIP_GZLOGS'}{'on'} /></td>
	<td width='30%'class='base'>$Lang::tr{'calamaris run as background task'}:</td>
	<td width='25%'><input type='checkbox' name='RUN_BACKGROUND' $checked{'RUN_BACKGROUND'}{'on'} /></td>
</tr>
</table>

<hr size='1'>

<table width='100%' border='0'>
<tr>
<td align='left'>&nbsp;</td>
<td width='33%' align='center'><input type='submit' name='ACTION' value='$Lang::tr{'calamaris create report'}' /></td>
<td width='33%' align='right'><sup><small><a href='http://joeyramone76.altervista.org/calamaris' target='_blank'>Calamaris $version for IPCop</a></small></sup></td>
</tr>

</table>

END
;

&Header::closebox();

&Header::openbox('100%', 'left', "$Lang::tr{'calamaris available reports'}:");

my @content=();
my @reports=();
my @reportdata=();
my $description;

undef @reports;

foreach (<$reportdir/*>)
{
	open (FILE, "$_");
	@content=<FILE>;
	if ($content[3] =~ /^Report\speriod/)
	{
		$description = timelocal(
			substr($content[4],31,2),
			substr($content[4],28,2),
			substr($content[4],25,2),
			substr($content[4],15,2),
			$monthidx{substr($content[4],18,3)},
			"20".substr($content[4],22,2));
		push(@reports,join("#",$description,substr($_,rindex($_,"/")+1),$content[3],$content[4]));
	}
	close FILE;
}

@reports=reverse(sort(@reports));


print <<END

<table width='100%' border='0'>
<tr>
END
;

if (@reports)
{
	print "<td><select name='REPORT' size='5'>\n";
	my $n=0;
	foreach (@reports)
	{
		@reportdata=split(/#/);
		print "\t<option ";
		if ($n eq '0') { print "selected "; $reportsettings{'REPORT'}=$reportdata[1]; $n++}
		print "value='$reportdata[1]'>$reportdata[2] &nbsp;-&nbsp; $reportdata[3]</option>\n";
	}
	print "</select></td>\n";
} else { print "<td><i>$Lang::tr{'calamaris no reports available'}</i></td>\n"; }

print <<END
</tr>
</table>
<hr size='1'>
<table width='100%' cellpadding='5' border='0'>
<tr>
<td><input type='submit' name='ACTION' value='$Lang::tr{'calamaris refresh list'}' /></td>
END
;

if (@reports)
{
print <<END
<td>&nbsp;</td>
<td>&nbsp;</td>
<td><input type='submit' name='ACTION' value='$Lang::tr{'calamaris view'}' /></td>
<td><input type='submit' name='ACTION' value='$Lang::tr{'export'}' /></td>
<td><input type='submit' name='ACTION' value='$Lang::tr{'delete'}' /></td>
<td width='95%'></td>
END
;
}

print <<END
</tr>
</table>
</form>
END
;

if (($reportsettings{'ACTION'} eq $Lang::tr{'calamaris view'}) && (-e "$reportdir/$reportfile"))
{
	&Header::closebox();
	&Header::openbox('100%', 'left', "$Lang::tr{'calamaris view report'}:");
	print "<pre>\n";
	open (FILE, "$reportdir/$reportfile");
	@content=<FILE>;
	close FILE;
	foreach (@content)
	{
		s/</\&lt;/;
		s/>/\&gt;/;
		print;
	}
	print "</pre>\n";
}

&Header::closebox();

&Header::closebigbox();

&Header::closepage();

# -------------------------------------------------------------------

sub check4updates
{
	if ((-e "/var/ipcop/red/active") && (-e $updflagfile) && (int(-M $updflagfile) > 7))
	{
		my @response=();;

		my $remote = IO::Socket::INET->new(
			PeerHost => 'joeyramone76.altervista.org',
			PeerPort => 'http(80)',
			Timeout  => 1
		);

		if ($remote)
		{
			print $remote "GET http://joeyramone76.altervista.org/calamaris/version/ipcop/latest HTTP/1.0\n";
			print $remote "User-Agent: Mozilla/4.0 (compatible; IPCop $General::version; $Lang::language; calamaris)\n\n";
			while (<$remote>) { push(@response,$_); }
			close $remote;
			if ($response[0] =~ /^HTTP\/\d+\.\d+\s200\sOK\s*$/)
			{
				system("touch $updflagfile");
				return "$response[$#response]";
			}
		}
	}
}

# -------------------------------------------------------------------
