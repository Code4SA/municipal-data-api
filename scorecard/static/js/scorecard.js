jQuery.support.cors = true;

// attach browser dimensions for help with charts and tables
window.browserWidth = document.documentElement.clientWidth;
window.browserHeight = document.documentElement.clientHeight;

$(document).ready(function(){
  // prepare ajax spinners
  $('body').append('<div id="body-spinner"></div>');
  var spinnerTarget = document.getElementById('body-spinner'),
      spinner = new Spinner();

  // FAQ sub-nav
  $('#faq-subnav').affix({
    offset: {
      top: function () {
        return (this.top = $('#faq-subnav').offset().top)
      },
      bottom: function () {
        return (this.bottom = $('#page-footer').outerHeight(true))
      }
    }
  })
  $('body').scrollspy({ target: '#faq-subnav' });

  if ($('#profile').length > 0) {
    // profile page stuff

    //Get page-nav offset from top of page
    var pagenavOffset = $('.page-nav-container').offset().top;

    //Affix page-nav to top of page on scroll
    $('.page-nav-container').affix({
      offset: {
        top: pagenavOffset
      }
    });

    //Expand page-nav once affixed
    $('.page-nav-container').on('affixed.bs.affix', function () {
      $('.page-nav-wrapper').addClass('expanded');
    });

    //Un-expand page-nav once nolonger affixed
    $('.page-nav-container').on('affixed-top.bs.affix', function () {
      $('.page-nav-wrapper').removeClass('expanded');
    });

    //Change active tab when scrolling using Bootstrap scrollspy.js
    $('body').scrollspy({ 
      target: '.page-nav-container',
      offset: 100
    });    

    //Easy scrolling (a link to #section will scroll to #section)
    $('.nav a[href^="#"]').on('click',function (e) {
      e.preventDefault();

      var target = this.hash;
      var $target = $(target);

      if ($target.length) {
        $('html, body').stop().animate({
            'scrollTop': $target.offset().top-15
        }, 300, 'swing', function() {
          window.location.hash = target;
        });
      }
    });

    $('.collapse')
      .on('shown.bs.collapse', function() {
        var $toggle = $('a.show-more[href="#' + this.id + '"]');
        $toggle.find('.fa').removeClass('fa-plus').addClass('fa-minus');
        // send google analytics event
        ga('send', 'event', 'show-more', this.id);
      })
      .on('hidden.bs.collapse', function() {
        var $toggle = $('a.show-more[href="#' + this.id + '"]');
        $toggle.find('.fa').removeClass('fa-minus').addClass('fa-plus');
      });

    // setup 'email municipality' link, by choosing the first two secretary emails
    var emails = $('#who-runs .contact-details a[href^="mailto:"]')
      .slice(0, 2)
      .map(function() { return this.href.split(':')[1]; });
    emails = _.compact(_.uniq(emails));

    var body = 'Browse Municipal Finance for ' + profileData.geography.name + ' at ' + window.location;

    var url = ('mailto:' +
      emails.join(',') +
      '?cc=feedback@municipalmoney.gov.za&body=\n\n\n' +
      encodeURIComponent(body));
    $('a.send-email').attr('href', url);
  }
});

$(function() {
  $iframe = $('.video-chooser iframe');

  $('.video-chooser .video-choices a').on('click', function(e) {
    e.preventDefault();
    var $btn = $(this);
    $btn.closest('.nav').find('li').removeClass('active');
    $btn.closest('li').addClass('active');

    $iframe.attr('src', this.href + "?autoplay=1");
    ga('send', 'event', 'play-video', $btn.data('lang'));
  });

  $('#video-modal')
    .on('show.bs.modal', function() {
      var $target = $('.video-chooser .video-choices .active a');
      $iframe.attr('src', $target.attr('href') + '?autoplay=1');
      ga('send', 'event', 'play-video', $target.data('lang'));
    })
    .on('hide.bs.modal', function() {
      $iframe.attr('src', '');
    });
});

$(function() {
  // track outbound links
  $('a[href^=http]').on('click', function(e) {
    ga('send', 'event', 'outbound-click', e.target.href);
  });
});

$(function() {
  var url = window.location.toString();

  // social buttons
  $('.fb-share').on('click', function(e) {
    e.preventDefault();

    window.open("https://www.facebook.com/sharer/sharer.php?u=" + encodeURIComponent(url),
                "share", "width=600, height=400, scrollbars=no");
                ga('send', 'social', 'facebook', 'share', url);
  });

  $('.twitter-share').on('click', function(e) {
    e.preventDefault();
    var tweet = $(this).data('tweet') || '';

    window.open("https://twitter.com/intent/tweet?" +
                "text=" + encodeURIComponent(tweet) +
                  "&url=" + encodeURIComponent(url),
                "share", "width=364, height=250, scrollbars=no");
                ga('send', 'social', 'twitter', 'share', url);
  });
});
