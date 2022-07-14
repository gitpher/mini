$(document).ready(function () {
    get_board()
});

function sign_out() {
    $.removeCookie('mytoken', {path: '/'});
    alert('로그아웃!')
    window.location.href = "/login"
}

function time2str(date) {
    let today = new Date()
    let time = (today - date) / 1000 / 60  // 분

    if (time < 60) {
        return parseInt(time) + "분 전"
    }
    time = time / 60  // 시간
    if (time < 24) {
        return parseInt(time) + "시간 전"
    }
    time = time / 24
    if (time < 7) {
        return parseInt(time) + "일 전"
    }
    return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`
}

function num2str(count) {
    if (count > 10000) {
        return parseInt(count / 1000) + "k"
    }
    if (count > 500) {
        return parseInt(count / 100) / 10 + "k"
    }
    if (count == 0) {
        return ""
    }
    return count
}


function toggle_like(board_id, type) {
    let $a_like = $(`#${board_id} a[aria-label='${type}']`)
    let $i_like = $a_like.find("i")
    let class_s = {"heart": "fa-heart", "star": "fa-star", "like": "fa-thumbs-up"}
    let class_o = {"heart": "fa-heart-o", "star": "fa-star-o", "like": "fa-thumbs-o-up"}
    if ($i_like.hasClass(class_s[type])) {
        $.ajax({
            type: "POST",
            url: "/api/like",
            data: {
                board_id_give: board_id,
                type_give: type,
                action_give: "unlike"
            },
            success: function (response) {
                $i_like.addClass(class_o[type]).removeClass(class_s[type])
                $a_like.find("span.like-num").text(num2str(response["count"]))
            }
        })
    } else {
        $.ajax({
            type: "POST",
            url: "/api/like",
            data: {
                board_id_give: board_id,
                type_give: type,
                action_give: "like"
            },
            success: function (response) {
                $i_like.addClass(class_s[type]).removeClass(class_o[type])
                $a_like.find("span.like-num").text(num2str(response["count"]))
            }
        })

    }
}

function get_board(username) {
    if (username == undefined) {
        username = ""
    }
    $('#boards-box').empty() // 리뷰 목록 초기화

    $.ajax({
      type: "GET",
      url: `/api/get_board?username_give=${username}`,
      data: {},
      success: function(response){
        if (response['result'] == 'success') {
            let rows = response['boards']
            for(let i=0; i<rows.length; i++) {
                let username = rows[i]['username']
                let title = rows[i]['title']
                let thumbnail = rows[i]['thumbnail_pic_real']
                let board_id = rows[i]['_id']
                let profile_pic = rows[i]['profile_pic_real']
                let date = new Date(rows[i]['date'])
                let date_better = time2str(date)
                let class_heart = rows[i]['heart_by_me'] ? "fa-heart": "fa-heart-o"
                let class_star = rows[i]['star_by_me'] ? "fa-star": "fa-star-o"
                let class_like = rows[i]['like_by_me'] ? "fa-thumbs-up" : "fa-thumbs-o-up"
                let count_heart = rows[i]['count_heart']
                let count_star = rows[i]['count_star']
                let count_like = rows[i]['count_like']

                let temp_html = `<div id="${board_id}" class="column is-one-quarter">
                                    <div class="card">
                                        <div class="card-image" onclick="location.href='/api/get_detail?board_id_give=${board_id}'"> <!-- 상세 페이지로 가기 onclick -->
                                            <figure class="image is-4by3">
                                                <img src="/static/pics/${thumbnail}" alt="Placeholder image">
                                            </figure>
                                        </div>
                                        <div class="card-content">
                                            <div class="media">
                                                <div class="media-left">
                                                    <figure class="image is-48x48 is-square">
                                                        <img src="/static/pics/${profile_pic}" alt="Placeholder image">
                                                    </figure>
                                                </div>
                                                <div class="media-content" onclick="location.href='/api/get_detail?board_id_give=${board_id}'"> <!-- 상세 페이지로 가기 -->
                                                    <p class="title is-4">${title}</p>
                                                    <p class="subtitle is-6">@${username}</p>
                                                </div>
                                            </div>

                                            <div class="content">
                                                <time>${date_better}</time>
                                                <br>
                                                <div class="level-right">
                                                    <a class="level-item is-sparta" aria-label="heart" onclick="toggle_like('${board_id}', 'heart')">
                                                        <span class="icon is-small"><i class="fa ${class_heart}" aria-hidden="true"></i></span>
                                                        &nbsp;<span class="like-num">${num2str(count_heart)}</span> 
                                                    </a>
                                                    <a class="level-item is-sparta" aria-label="star" onclick="toggle_like('${board_id}', 'star')">
                                                        <span class="icon is-small"><i class="fa ${class_star}" aria-hidden="true"></i></span>
                                                        &nbsp;<span class="like-num">${num2str(count_star)}</span>
                                                    </a>
                                                    <a class="level-item is-sparta" aria-label="like" onclick="toggle_like('${board_id}', 'like')">
                                                        <span class="icon is-small"><i class="fa ${class_like}" aria-hidden="true"></i></span>
                                                        &nbsp;<span class="like-num">${num2str(count_like)}</span>
                                                    </a>
                                                </div>
                                                
                                                
                                            </div>
                                        </div>
                                    </div>
                                </div>`

                $('#boards-box').append(temp_html) // 리뷰 목록 추가
            }
        }
      }
    });
}

function update_profile() {
    let name = $('#input-name').val()
    let file = $('#input-pic')[0].files[0]
    let about = $("#textarea-about").val()
    let form_data = new FormData()
    form_data.append("file_give", file)
    form_data.append("name_give", name)
    form_data.append("about_give", about)

    $.ajax({
        type       : "POST",
        url        : "/update_profile",
        data       : form_data,
        cache      : false,
        contentType: false,
        processData: false,
        success    : function (response) {
            if (response["result"] == "success") {
                alert(response["msg"])
                window.location.reload()

            }
        }
    });
}
