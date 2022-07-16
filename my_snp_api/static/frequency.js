function buildTable(data){
	var table = document.getElementById('frequency-table')
    table.innerHTML = ''
	for (var i=0; i<data.length; i++){
		var row = `<tr>
						<td>${data[i].trait}</td>
						<td>${data[i].selected_rare}</td>
                        <td>${data[i].trait_count}</td>
						<td>${data[i].selected_pct}</td>
				  </tr>`
		table.innerHTML += row
	}
}

function handleDisplay_Frequency(icon_remove_string, answer, icon_add, icon_remove) {
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

$('#accordionlink_frequency').click(function() {
    handleDisplay_Frequency("icon_remove_frequency", '#answer_frequency', '#icon_add_frequency', '#icon_remove_frequency');
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

$("#id_population").change(function () {
const url = $("#population_form").attr("population_url");
const populationId = $(this).val();
console.log(populationId);

$.ajax({
    url: url,
    data : {
        'population_id': populationId
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

window.onload = function () {
    const url = "{% url 'loadFrequency-view' %}";
    $.ajax({
        url: url,
        data : {},
        success: function (response) {
            myArray = response.data
            buildTable(myArray)
        },
        error: function(error){
           console.log(error)
        },
        })
}