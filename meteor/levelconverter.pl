#!/usr/bin/perl -w

use XML::Parser;
use Data::Dumper;


$p1 = new XML::Parser(Style => 'Tree');
my $level = 0;
sub processLevel
{
    my $n = shift;
    my $tree = $p1->parsefile("level$n.tmx");
    $tree = $tree->[1];    
    my $elem;
    $level = $n;
    while(defined($elem = shift @{$tree}))
    {
        print "Process keyword $elem\n";
        if($elem eq "layer")
        {
            my $data = shift @$tree;
            processLayer($data);
        }
    }
}

open(PYTHON, ">levels.py");
my $l = 1;
while(-f "level$l.tmx") {
    processLevel($l);
    $l += 1;
}



sub processData
{
    my $name = shift;
    my $text = shift;
    if($name =~ / /) {
	print "Error: map $level contains a layer with a space in the name.\n";
	print "This would create invalid Python.\n";
	exit(1);
    }
    print PYTHON "level$level$name = [\n";
    my @rows = split("\n",$text);
    my $firstRow = 1;
    for my $r(@rows) {
        if($firstRow == 0) { print PYTHON ","; }
        if($r =~ /,/) {
            $r =~ s/,\s*$//;
            print PYTHON " [ $r ]\n";
            $firstRow = 0;
        }
    }
    print PYTHON "]\n";
}

sub processLayer
{
    my $layer = shift;
    my $elem;
    my $info = shift @{$layer};
    my $name = $info->{name};
    print("Processing layer $name:\n");
    while(defined($elem = shift @{$layer}))
    {
        print "Processing layer element $elem\n";
        if($elem eq "data")
        {
            my $data = shift @$layer;
            $data = $data->[2];
            processData($name,$data);
        }
    }
}





    close PYTHON;
