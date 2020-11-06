// Load posts onto the page.
document.addEventListener('DOMContentLoaded', function () {
    load_all_posts(1)
});

/**
 * Load posts and display them to the current page. User data and filters required
 * are supplied in the dataset of #all_posts div. If posts are successful, loads the paginator.
 * @param page - the current page required by paginator.
 */
function load_all_posts(page = 1) {
    // Data required to load and/or filter the list of posts.
    const element = document.querySelector('#all_posts');
    const logged_in = (element.dataset.loggedin === 'True');
    const user_id = element.dataset.userid;
    const filter = element.dataset.filter;
    let url = `/posts/${page}/${filter}/${user_id}`;
    const profile_id = (filter === 'profile' ? element.dataset.profileid : 0);
    if (profile_id != 0) {
        url = `/posts/${page}/${filter}/${profile_id}`;
    }

    // Get all posts and display them.
    fetch(`${url}`).then(response => {
        // Detect errors from the API.
        if (!response.ok) {
            throw Error(response.status + ' - ' + response.statusText);
        }
        return response.json();
    }).then((posts) => {
        // Reset the page content and check for posts.
        element.innerHTML = '';
        if (posts['page_objects'].length == 0) {
            element.innerHTML = `<h5 class="mt-3 ml-3">No Posts to Display.</h5>`
        }
        posts['page_objects'].forEach(function (post) {
            //  Indicators needed when displaying the list of posts.
            const post_creator = post.creator_id === parseInt(user_id);
            const liked = logged_in && post.likes.includes(parseInt(user_id));

            // Setup a list item for each post.
            const list_group_item = document.createElement('li');
            list_group_item.className = const_values.li;

            // Create a div to format and display the post content.
            const post_div = document.createElement('div');
            post_div.id = `post-div-${post.id}`;
            let like_image = (liked ? 'heart.png' : 'heart_dark.png');
            let post_content = `<div class="${const_values.div}"><h5 class="mb-0">`
                + `<a href="/profile/${post.creator_id}">${post.creator}</a></h5></div>`
                // + `<img src="/static/network/${like_image}" height="20" class="mr-3"/></div>`
                + `<div class="${const_values.div}"><small>${post.create_date}</small>`
                + `<small>${post.total_likes} like(s)</small></div>`
                + `<div class="${const_values.div}"><p>${post.content}</p></div>`;
            post_div.innerHTML = post_content;
            list_group_item.append(post_div);

            const button_div = document.createElement('div');
            button_div.id = `button-div-${post.id}`;
            // Add the Edit button and (hidden) Edit form if this User created the post.
            if (logged_in && post_creator) {
                const edit_div = document.createElement('div');
                edit_div.style.display = 'none';
                edit_div.id = `edit-div-${post.id}`;
                let form_html = `<textarea class="form-control" id="content-${post.id}" name="post_content">`
                    + `${post.content}</textarea><div class="invalid-feedback font-weight-bold" `
                    + `id="update-alert-${post.id}">There was an error: Please include content for your post.</div>`;
                edit_div.innerHTML = form_html;
                edit_div.append(create_button(const_values.update, post));
                list_group_item.append(edit_div);
                button_div.append(create_button(const_values.edit, post));
            }
            // Add the Like button for logged in Users.
            if (logged_in) {
                button_div.append(create_button(const_values.like, post, liked));
            }
            list_group_item.append(button_div);
            element.append(list_group_item);
        })
        load_paginator(posts['page'], posts['num_pages']);
    })

}

/**
 * Creates and returns a button element with default attributes, id and dataset items. Will also
 * add event listeners specific to the button requested.
 * @param type - type of button requested: Edit, Update or Like.
 * @param post - Post item the button will be associated with.
 * @param liked - indicates if current User has liked this post or not.
 * @returns {HTMLButtonElement}
 */
function create_button(type, post, liked) {
    // Create a button with default attributes.
    let button = document.createElement('button');
    button.className = const_values.btn;
    button.id = `${type}-${post.id}`;
    button.dataset.post_id = `${post.id}`;
    button.innerText = type;

    switch (type) {
        case const_values.edit:
            // Show & Hide div elements to allow Post editing.
            button.addEventListener('click', () => {
                document.querySelector(`#edit-div-${post.id}`).style.display = 'block';
                document.querySelector(`#post-div-${post.id}`).style.display = 'none';
                document.querySelector(`#button-div-${post.id}`).style.display = 'none';
            });
            break;
        case const_values.update:
            // Save the updated content.
            button.addEventListener('click', function () {
                update_post(post.id);
            });
            break;
        case const_values.like:
            button.addEventListener('click', function () {
                toggle_like_post(post.id)
            });
            button.innerText = (liked ? 'Unlike' : 'Like');
            break;
    }
    return button;
}

/**
 * Store updated content for a given post.
 * @param post_id - post to be updates.
 * @returns {boolean}
 */
function update_post(post_id) {
    // Security token required for POST request to API.
    const token = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    // Validate there is content in the post.
    const new_content = document.querySelector('#content-' + post_id).value;
    if (!new_content) throw Error('Please enter content for this post.');

    fetch('/update_post', {
        method: 'POST',
        headers: {
            'X-CSRFToken': token,
        },
        body: JSON.stringify({
            content: new_content,
            id: post_id
        })
    }).then(response => {
        if (!response.ok) {
            data = response.json()
            throw Error(response.status + ' - ' + response.statusText);
        }
        // Reset the page with a successful update.
        document.querySelector(`#edit-div-${post_id}`).style.display = 'none';
        document.querySelector(`#post-div-${post_id}`).style.display = 'block';
        document.querySelector(`#button-div-${post_id}`).style.display = 'block';
        document.querySelector(`#content-${post_id}`).className = 'form-control is-valid';
        const paginator = document.querySelector('#paginator');
        load_all_posts(paginator.dataset.current_page);
    }).catch((error) => {
        // Display failures in an alert.
        document.querySelector(`#update-alert-${post_id}`).textContent = error;
        document.querySelector(`#content-${post_id}`).className = 'form-control is-invalid';
        console.log(error);
    })
    //Stop form from submitting.
    return false;
}

/**
 * Create and display the paginator for list of posts.
 * @param page - current page the user is on.
 * @param total_pages - count of pages given 10 posts per page.
 */
function load_paginator(page, total_pages) {
    const element = document.querySelector('#paginator');
    element.dataset.current_page = page;
    element.innerHTML = '';
    // No need for a paginator if there is but one page.
    if (total_pages <= 1) return;


    // Create the prev button.
    const prev_li = document.createElement('li');
    prev_li.className = 'page-item';

    const prev_link = document.createElement('a');
    prev_link.innerText = 'previous';

    if (page > 1) {
        prev_li.className = 'page-item';
        prev_link.className = 'page-link';
        prev_link.href = '#';
        prev_link.addEventListener('click', function () {
            load_all_posts(page - 1)
        })
        prev_li.append(prev_link);
        element.append(prev_li);
    } else {
        prev_li.className = 'page-item disabled';
        prev_link.className = 'page-link disabled';
    }


    // Add page links in between previous and next links.
    for (let p = 0; p < total_pages; p++) {
        const list_item = document.createElement('li');
        list_item.className = (p + 1 === page ? 'page-item active' : 'page-item');
        const anchor = document.createElement('a');
        anchor.className = 'page-link';
        anchor.innerHTML = (p + 1).toString();
        anchor.href = '#';
        anchor.addEventListener('click', function () {
            load_all_posts(p + 1)
        })
        list_item.append(anchor);
        element.append(list_item);
    }

    // Create the next button.
    const next_li = document.createElement('li');
    next_li.className = 'page-item';

    const next_link = document.createElement('a');
    next_link.innerText = 'next';

    if (total_pages > page) {
        next_li.className = 'page-item';
        next_link.className = 'page-link';
        next_link.href = '#';
        next_link.addEventListener('click', function () {
            load_all_posts(page + 1)
        })
    } else {
        next_li.className = 'page-item disabled';
        next_link.className = 'page-link disabled';
    }
    next_li.append(next_link);
    element.append(next_li);
}


/**
 * Add or remove a Like to the Post for the current User.
 * @param post_id
 */
function toggle_like_post(post_id) {
    fetch('/toggle_like_post/' + post_id)
        .then(response => {
            if (!response.ok) {
                throw Error(response.status + ' - ' + response.statusText);
            }
            return response.json()
        }).then((data) => {
        const paginator = document.querySelector('#paginator');
        load_all_posts(paginator.dataset.current_page)
    })
        .catch((error) => {
            console.log(error)
            const button_div = document.querySelector(`#button-div-${post_id}`);
            const alert_div = document.createElement('div');
            alert_div.className = 'alert alert-danger';
            alert_div.textContent = 'Error: ' + error.message;
            button_div.appendChild(alert_div);
        })
}

// Constants.
const const_values = {
    li: "list-group-item flex-column align-items-start",
    btn: 'ml-1 mr-2 btn btn-outline-info mt-1 btn-sm',
    div: 'd-flex w-100 justify-content-between',
    edit: 'Edit',
    update: 'Update',
    follow: 'Follow',
    like: 'Like',
    danger: 'alert alert-danger alert-dismissible'
}
