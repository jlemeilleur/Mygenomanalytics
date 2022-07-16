function handleDisplay(num, icon_remove_string, answer, icon_add, icon_remove) {
    let ion_remove = document.getElementById(icon_remove_string);
    let style = getComputedStyle(ion_remove);
    if (style.display=='block') {
        $(answer).css({
            'display': 'none'
        })
        $(icon_add).css({
            'display': 'block'
        })
        $(icon_remove).css({
            'display': 'none'
        })
    }
    else if (style.display=='none') {
        $(answer).css({
            'display': 'block'
        })
        $(icon_add).css({
            'display': 'none'
        })
        $(icon_remove).css({
            'display': 'block'
        })
    };
    for (let i = 1; i < 11; i++) {
        let ion_remove_other = document.getElementById("icon_remove" + i.toString());
        let style = getComputedStyle(ion_remove_other);
        if (i != num) {
            if (style.display=='block') {
            $('#icon_remove' + i.toString()).css({
                'display': 'none'
            })}
            if (style.display=='none') {
            $('#icon_add' + i.toString()).css({
                'display': 'block'
            })}
        }
    }
}

$('#accordionlink1').click(function() {
    handleDisplay(1, "icon_remove1", '#answer1', '#icon_add1', '#icon_remove1');
});
$('#accordionlink2').click(function() {
    handleDisplay(2, "icon_remove2", '#answer2', '#icon_add2', '#icon_remove2');
});
$('#accordionlink3').click(function() {
    handleDisplay(3, "icon_remove3", '#answer3', '#icon_add3', '#icon_remove3');
});
$('#accordionlink4').click(function() {
    handleDisplay(4, "icon_remove4", '#answer4', '#icon_add4', '#icon_remove4');
});
$('#accordionlink5').click(function() {
    handleDisplay(5, "icon_remove5", '#answer5', '#icon_add5', '#icon_remove5');
});
$('#accordionlink6').click(function() {
    handleDisplay(6, "icon_remove6", '#answer6', '#icon_add6', '#icon_remove6');
});
$('#accordionlink7').click(function() {
    handleDisplay(7, "icon_remove7", '#answer7', '#icon_add7', '#icon_remove7');
});
$('#accordionlink8').click(function() {
    handleDisplay(8, "icon_remove8", '#answer8', '#icon_add8', '#icon_remove8');
});
$('#accordionlink9').click(function() {
    handleDisplay(9, "icon_remove9", '#answer9', '#icon_add9', '#icon_remove9');
});
$('#accordionlink10').click(function() {
    handleDisplay(10, "icon_remove10", '#answer10', '#icon_add10', '#icon_remove10');
});