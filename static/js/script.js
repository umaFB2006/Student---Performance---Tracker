/* ==========================
DARK MODE
========================== */

function toggleTheme(){

document.body.classList.toggle("dark-mode");

if(document.body.classList.contains("dark-mode")){

localStorage.setItem("theme","dark");

}
else{

localStorage.setItem("theme","light");

}

}

/* ==========================
LOAD SAVED THEME
========================== */

window.onload=function(){

if(localStorage.getItem("theme")==="dark"){

document.body.classList.add("dark-mode");

}

};

/* ==========================
SEARCH TABLE
========================== */

function searchTable(){

let input=
document.getElementById("searchInput");

let filter=
input.value.toUpperCase();

let table=
document.getElementById("studentTable");

let tr=
table.getElementsByTagName("tr");

for(let i=1;i<tr.length;i++){

let td=
tr[i].getElementsByTagName("td")[0];

if(td){

let txt=
td.textContent || td.innerText;

if(txt.toUpperCase().indexOf(filter)>-1){

tr[i].style.display="";

}
else{

tr[i].style.display="none";

}

}

}

}

/* ==========================
SORT TABLE
========================== */

function sortTable(){

let table=
document.getElementById("studentTable");

let switching=true;

while(switching){

switching=false;

let rows=
table.rows;

for(let i=1;i<rows.length-1;i++){

let shouldSwitch=false;

let x=
rows[i].getElementsByTagName("TD")[0];

let y=
rows[i+1].getElementsByTagName("TD")[0];

if(
x.innerHTML.toLowerCase()
>
y.innerHTML.toLowerCase()
){

shouldSwitch=true;
break;

}

}

if(shouldSwitch){

rows[i].parentNode.insertBefore(
rows[i+1],
rows[i]
);

switching=true;

}

}

}