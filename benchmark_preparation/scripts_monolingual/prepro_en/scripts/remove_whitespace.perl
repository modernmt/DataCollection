#!/usr/bin/perl -w

binmode(STDIN, ":utf8");
binmode(STDOUT, ":utf8");
binmode(STDERR, ":utf8");

use strict;

while(<STDIN>) {
    chop;
    my $text = $_;
    $text =~ s/^\s+//g;
    $text =~ s/\s+$//g;
    $text =~ s/\s\s+$/ /g;
    if ($text !~ /^\s*$/ ) {
        print $text."\n";
    }
}
