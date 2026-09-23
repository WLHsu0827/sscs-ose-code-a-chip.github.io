proc box_um {x1 y1 x2 y2} {
    box values ${x1}um ${y1}um ${x2}um ${y2}um
}

proc pin_order {} {
    set i 1
    foreach pin {D G S B} {
        port $pin index $i
        incr i
    }
}

proc save_and_check {cell} {
    select top cell
    expand
    box values {*}[select bbox]
    drc on
    drc check
    drc catchup
    set count 0
    set reasons [drc listall why]
    foreach {reason rectangles} $reasons {
        incr count [llength $rectangles]
    }
    set report [open ${cell}.drc.txt w]
    puts $report "cell: $cell"
    puts $report "technology: [tech name]"
    puts $report "drc_style: [drc style]"
    puts $report "count: $count"
    puts $report $reasons
    close $report
    puts "PREFLIGHT_DRC $cell $count"
    save $cell
    gds write ${cell}.gds
}

proc connectivity {cell} {
    extract style ngspice
    extract no resistance
    extract do capacitance
    extract do coupling
    extract all
    ext2spice lvs
    ext2spice blackbox off
    ext2spice hierarchy off
    ext2spice merge none
    ext2spice scale off
    ext2spice -o ${cell}.lvs.spice
}

proc routed_probe {cell length} {
    findlabel D
    set terminal [sky130::getbox]
    set x [expr {([lindex $terminal 0] + [lindex $terminal 2]) / 2.0}]
    set y [expr {([lindex $terminal 1] + [lindex $terminal 3]) / 2.0}]
    # Move the external drain port to the far end, not an ideal short alias.
    erase labels
    box_um [expr {$x - 0.13}] [expr {$y - 0.13}] \
        [expr {$x + 0.13}] [expr {$y + 0.13}]
    sky130::via1_draw
    set left [expr {$x - $length}]
    set top [expr {$y + 10.0}]
    box_um $left [expr {$y - 0.18}] [expr {$x + 0.18}] [expr {$y + 0.18}]
    paint metal2
    box_um $left [expr {$y - 0.18}] [expr {$left + 0.36}] [expr {$top + 0.18}]
    paint metal2
    box_um $left [expr {$top - 0.18}] [expr {$x + 0.18}] [expr {$top + 0.18}]
    paint metal2
    box_um $x $top $x $top
    label D c metal2
    port make 1
    pin_order
    save_and_check $cell
    connectivity $cell

    ext2spice extresist off
    ext2spice cthresh 0
    ext2spice -y 6 -o ${cell}.c.spice

    # These are milliohms (threshold/minresist) and picoseconds (mindelay).
    # Do not use the obsolete extresist tolerance setting.
    extresist threshold 0
    extresist minresist 0
    extresist mindelay 0
    extresist simplify off
    extresist blackbox off
    extract do resistance
    extract all
    ext2spice extresist on
    ext2spice cthresh 0
    ext2spice rthresh 0
    ext2spice -y 6 -o ${cell}.rc.spice
}

proc main {} {
    if {[tech name] ne "sky130A"} {error "The genuine sky130A deck did not load"}
    random seed 1
    drc euclidean on
    drc style drc(full)
    set cell $::env(PREFLIGHT_CELL)
    load $cell -silent
    box_um 0 0 0 0
    switch -- $::env(PREFLIGHT_MODE) {
        device {
            set model $::env(PREFLIGHT_MODEL)
            set w $::env(PREFLIGHT_WIDTH)
            set l $::env(PREFLIGHT_LENGTH)
            set parameters [dict merge [sky130::${model}_defaults] \
                [dict create w $w l $l nf 1 m 1 guard 1 doports 1 topc 1 botc 0]]
            set checked [sky130::${model}_check $parameters]
            foreach key {w l nf m} {
                if {[dict get $parameters $key] != [dict get $checked $key]} {
                    error "PCell changed requested $key; refusing a clamped dimension"
                }
            }
            sky130::${model}_draw $checked
            pin_order
            save_and_check $cell
            connectivity $cell
        }
        route {
            routed_probe $cell $::env(PREFLIGHT_ROUTE_LENGTH)
        }
        spacing {
            box_um 0 0 1 1
            paint metal1
            box_um 1.07 0 2.07 1
            paint metal1
            save_and_check $cell
        }
        default {error "Unknown preflight mode"}
    }
    puts "PREFLIGHT_MAGIC_COMPLETE $cell"
}

if {[catch {main} message options]} {
    puts stderr "PREFLIGHT_MAGIC_ERROR: $message"
    puts stderr [dict get $options -errorinfo]
    exit 1
}
exit 0
