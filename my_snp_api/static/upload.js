var clickCount=0;
const genomeFileElement = document.getElementById('id_upload_genome_file')
const ancestryFileElement = document.getElementById('id_upload_ancestry_file')
const GenomeFieldsetElement = document.getElementById('GenomeFieldset')
const AncestryFieldsetElement = document.getElementById('AncestryFieldset')
const textElement = document.getElementById('textwrapper')
genomeFileElement.addEventListener("click", () => {
    document.getElementById("waitMessage").innerHTML = "";
    clickCount+=1;
});
ancestryFileElement.addEventListener("click", () => {
    document.getElementById("waitMessage").innerHTML = "";
    clickCount+=1;
});
GenomeFieldsetElement.addEventListener("click", () => {
    document.getElementById("waitMessage").innerHTML = "";
});
AncestryFieldsetElement.addEventListener("click", () => {
    document.getElementById("waitMessage").innerHTML = "";
});
textElement.addEventListener("click", () => {
    document.getElementById("waitMessage").innerHTML = "";
});
function displayWait() {
if (clickCount>=2){
    clickCount=0
    document.getElementById("waitMessage").innerHTML = "Loading should take about 30 seconds (maximum 1 minute)...";
}}