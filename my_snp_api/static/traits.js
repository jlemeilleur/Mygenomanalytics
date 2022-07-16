function handleDisplay_Trait(icon_remove_string, answer, icon_add, icon_remove) {
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

$('#accordionlink_trait').click(function() {
    handleDisplay_Trait("icon_remove_trait", '#answer_trait', '#icon_add_trait', '#icon_remove_trait');
});

function buildTable(data){
	var table = document.getElementById('master-table')
    table.innerHTML = ''
	for (var i=0; i<data.length; i++){
		var row = `<tr>
						<td>${data[i].Ethnicity}</td>
						<td>${data[i].Father}</td>
						<td>${data[i].Mother}</td>
						<td>${data[i].Combined}</td>
				  </tr>`
		table.innerHTML += row
	}
}

var FirstRunFlag = 1;
$("#id_trait").change(function () {
const url = $("#trait_form").attr("trait_url");
const traitId = $(this).val();
 if (FirstRunFlag) {
    var x = document.getElementById("id_trait");
    x.remove(0);
    FirstRunFlag = 0
}

$.ajax({
    url: url,
    data : {
        'trait_id': traitId
    },
    success: function (response) {
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
