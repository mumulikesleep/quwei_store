var vm = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        username: getCookie('username'),
        score: 0,//满意度评分
        display_score: 0,
        final_score: 0,
    },
    methods: {
        on_stars_mouseover: function(score){
            this.score = score;
            this.display_score = score * 20;
        },
        on_stars_mouseout: function() {
            this.score = this.final_score;
            this.display_score = this.final_score * 20;
        },
        on_stars_click: function(score) {
            this.final_score = score;
        },
        //表单提交
        on_submit: function(){
            this.display_score = display_score;
            window.event.returnValue = false;
        }
    }
});