let section = document.getElementById('sect')
let html = ''
for(var i=0 ; i<1 ; i++){
	html += `
	<div class="room11__container room">
	<div class="room11__left">
	  <div class="room11__head drroom">
	Sample Collection
		<br />
		<span></span>
	  </div>

	  <div class="room11__content content quelist">
		
	  </div>
	</div>

	<!-- room11 name container -->
	<div class="room11__dr__name">
	  <div class="room11__dr__name__head drname">Called</div>
	   <div class="current_p">
	  <div class="room3__dr__name__room__number "></div>
	  <div class="room3__dr__second__name"></div>
	</div>
	</div>
  </div>
	`
	
}
section.innerHTML = html
const url = window.location.href
let url_sp = url.split("/").pop()
let hall = url_sp





const baseUrl = `${window.location.protocol}//${window.location.host}`;
        


setInterval(() => {
  const options = {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json;charset=UTF-8',
      'Authorization': 'token 9716d5613f8642e:5eb6c6cafb793eb'
    },
    body: JSON.stringify({
      hall: hall,
   
    })
  };
  fetch(`${baseUrl}/api/method/his.www.screen.screen.get_collection` , options)
	.then(response => response.json())
	.then(r => {
    console.log(r)


            
        
     



let que_list=r.message[0]
let called_que = r.message[1]




// let que_list=r.message[0]
//  let que_list =
//   [

//  {"token_no" : 1 , "patient_name" : "Daacad" ,"practitioner_name" : "Dr Jaamac" } ,
//   {"token_no" : 1 , "patient_name" : "Farax Cali Axmed" ,"practitioner_name" : "Dr Rooble" },
//   {"token_no" : 1 , "patient_name" : "Nuur Jaamac" ,"practitioner_name" : "Dr Abdiwahaab" },
//    {"token_no" : 2 , "patient_name" : "Abdixakiin" ,"practitioner_name" : "Dr Daacadd"}, 
//      {"token_no" : 2 , "patient_name" : "Cabdikariin" ,"practitioner_name" : "Dr Rooble" },



//   ]
doc_lists = {}
doc_list_que = []
let room_elm =  document.querySelectorAll(".drroom")
let doctor_elm =  document.querySelectorAll(".drname")
let que_list_elment =  document.querySelectorAll(".quelist")




// Called Que
// let called_que = que_list.filter(function(que) {
//     return que.que_steps == "Called";
//   });




// Called Que for Each Doctor
if(que_list){
  que_list.forEach( que => {
    if(doc_lists[`${que.practitioner_name}`]){
        
    doc_lists[`${que.practitioner_name}`].push(que)
        
  }
  else{
  
    doc_lists[`${que.practitioner_name}`] = []
    doc_lists[`${que.practitioner_name}`].push(que)
  
  }
  })
}



// que_list = que_list.filter(function(que) {
//   return que.que_steps != "Called";
// });
que_list.sort(function(a, b) {
  return a.token_no - b.token_no;
});






let current_p =  document.querySelectorAll(".current_p")

current_p.forEach((elm , index)=>{
 
  
   
     
        // alert(index)
        // alert(called_que[`${dotors[index]}`])
        // console.log(called_que[`${dotors[index]}`][index].patient_name)
        if(called_que.length){
          // alert()
        
          current_p[0].innerHTML = `
    
          <div style ="color:white" class="room3__dr__name__room__number ">${called_que[0].token_no}</div>
            <div style ="color:white" class="room3__dr__second__name">${called_que[0].patient_name}</div>

    `

        }
            
     
    
 
    //     if(called_que.length){
    //       if(called_que[index]){
    //         if(called_que[index].practitioner_name){
          
    //         current_p[index].innerHTML = `
    
    //         <div style ="color:white" class="room3__dr__name__room__number ">${called_que[index].token_no}</div>
    //           <div style ="color:white" class="room3__dr__second__name">${called_que[index].patient_name}</div>
  
    //   `
              
         
    //         }
    //         // alert(called_que[index].patient_name)
        
    //       }
               
    // }

  
 
})

          

// doctor_elm.forEach((elm , index) => {
//     // elm.html(rooms[index])
//     if(rooms[index]){
//       elm.innerHTML = rooms[index].practitioner_name
//     }
   

// })
que_list_elment[0].innerHTML = ''
// que_list_elment[1].innerHTML = ''
// que_list_elment[2].innerHTML = ''
// que_list_elment[3].innerHTML = ''
que_list.forEach((elm , index) => {

    // elm.html(rooms[index])
    // alert(dotors.indexOf(`${elm.practitioner_name}`))
    
   
    que_list_elment[0].innerHTML += `
      
    <div class="room3__list list">
                <span>${elm.token_no}</span>
                <span>${elm.patient_name}</span>
    </div>

    `
    }

)


    
    


})
}, 1000);


            



