function handleDisplay_Ancestry(icon_remove_string, answer, icon_add, icon_remove) {
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
}

$('#accordionlink_ancestry').click(function() {
    handleDisplay_Ancestry("icon_remove_ancestry", '#answer_ancestry', '#icon_add_ancestry', '#icon_remove_ancestry');
});

function buildTable(data){
	var table = document.getElementById('ancestry-table')
    table.innerHTML = ''
	for (var i=0; i<data.length; i++){
		var row = `<tr>
						<td>${data[i].trait}</td>
						<td>${data[i].Total_count}</td>
						<td>${data[i].percentage_combined}</td>
				  </tr>`
		table.innerHTML += row
	}
}


var FirstRunFlag = 1;
$("#id_ancestry").change(function () {
const url = $("#ancestry_form").attr("ancestry_url");
const ancestryId = $(this).val();
 if (FirstRunFlag) {
    var x = document.getElementById("id_ancestry");
    x.remove(0);
    FirstRunFlag = 0
}

$.ajax({
    url: url,
    data : {
        'ancestry_id': ancestryId
    },
    success: function (response) {
        console.log(response);
        myArray = response.data
        buildTable(myArray)
    },
    error: function(error){
       console.log(error)
    },
    })
});


$("#id_pvalue").change(function () {
const url = $("#pvalue_form").attr("pvalue_url");
const pvalueId = $(this).val();
console.log(pvalueId);

$.ajax({
    url: url,
    data : {
        'pvalue_id': pvalueId
    },
    success: function (response) {
        console.log(response);
        myArray = response.data
        buildTable(myArray)
    },
    error: function(error){
       console.log(error)
    },
    })
});
