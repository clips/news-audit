/* Simple example with PhantomJS, a "headless" browser:
 * http://phantomjs.org
 *
 * We downloaded phantomjs-2.1.1-macosx,
 * and simply put that folder in the same folder as this script to make it work.
 *
 * We can then execute this script from the shell with:
 * > phantomjs-2.1.1-macosx/bin/phantomjs screen1.js
 *
 * The script takes a URL and generates a screenshot of the site, in this folder.
 * We could also generate the code below from Python, for each newspaper article
 * we have, and automatically construct a corpus for image analysis.
 */

var url = 'http://thefederalistpapers.org/us/boom-brutal-meme-shows-why-leftist-hysteria-over-travel-ban-will-backfire';

var page = require('webpage').create();

page.viewportSize = { 
	width  : 1024, 
	height : 768 
};

page.clipRect = { 
	top    : 0, 
	left   : 0, 
	width  : 1024, 
	height : 768 
};

page.open(url, function() {
  page.render('test.png');
  phantom.exit();
});