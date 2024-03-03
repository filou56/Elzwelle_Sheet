#! /usr/bin/perl

$pins = "";

for ($i=0; $i<20; $i++) {
    $pins = $pins.sprintf("%4d,",int(rand(8999)) + 1000);
}

chop($pins);

print($pins);


