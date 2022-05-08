function dragStartHandler(event) {
    event.dataTransfer.setData("text",event.target.innerHTML);
    event.dataTransfer.dropEffect = "copy";
}

function dropHandler(event) {
    var data = event.dataTransfer.getData("text");
    event.target.innerHTML = event.target.innerHTML + data;
    
}

function dragOverHandler(event) {
    event.dataTransfer.dropEffect = "copy";
}

// function retryEmail() {
//     fetch('/campaign/email/entry')
// }

