ranges =[];
crnt_range = [];

function changeVar(e){
  crnt_range[this].innerText = e.currentTarget.value;

}


window.addEventListener('load',function(){
  ranges = document.querySelectorAll('.range_bar');
  crnt_range = document.querySelectorAll('.range_display');
  
  for(var i = 0; i < ranges.length; i++){
    crnt_range[i].innerText = ranges[i].value;
    ranges[i].addEventListener('input', changeVar.bind(i),false);
  }

},false);
