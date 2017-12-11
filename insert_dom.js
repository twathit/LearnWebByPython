// sort list:
var i,j,c,
    list=document.getElementById('test-list');
for (i=0;i<list.children.length;i++){
	for (j=i+1;j<list.children.length;j++){
		if (list.children[i].innerText > list.children[j].innerText){
			list.insertBefore(list.children[j],list.children[i]);
		}
	}
}
;(function () {
    var
        arr, i,
        t = document.getElementById('test-list');
    if (t && t.children && t.children.length === 5) {
        arr = [];
        for (i=0; i<t.children.length; i++) {
            arr.push(t.children[i].innerText);
        }
        if (arr.toString() === ['Haskell', 'JavaScript', 'Python', 'Ruby', 'Scheme'].toString()) {
            alert('测试通过!');
        }
        else {
            alert('测试失败: ' + arr.toString());
        }
    }
    else {
        alert('测试失败!');
    }
})();