Databases Final Project
Gary Chen gc2676
Margaret Qian myq2000

PostgresSQL account where our datababse is:
Username: gc2676

URL: http://104.196.221.126:8111/

Description:
Boba Tea cafe shop database web application
We implemented these features:
Users: 
	-login/logout
	-create account with username/password
	-check into cafe shops with your account
	-leave ratings/reviews on cafe shops with your account
	-view user profile (shows name, username, boba status, cafes checked into)

List of all cafe shops:
	-shows details of cafes when you click in
	-details include name, cafe info, location, reviews, ratings

Add cafe:
	-Add cafe into the database, enter features such as name, price range, location, phone number, etc.

Search bar:
	-Filter cafes by name (exact match including capitalization)
	-Filter cafes by neighborhood (also exact match)
	-Filter cafes by available time (in minutes, current time until closing time)
	


Two most interesting features:
Cafe detail:
	-Click on a cafe from the main page or from search results.
	-Page will show details on the cafe, location, previous ratings and reviews
	-You can leave a rating for the category you choose
	-You can write a review for the cafe
	-Ratings and reviews are under user's account name
	-You can check in to a cafe, if you have already checked in the option is greyed out
	-If user is not logged in the option to leave a rating and review doesn't show up

Search Bar:
	-Ability to search 3 categories, name, neighborhood and available time.
	-When there is a match cafe options show up and you can click into them to get to the cafe detail page.
	-Searching by name and neighborhood require an exact match (including capitalization)
	-Searching by time (in minutes) brings up cafe shops still open from now until the specified available time you have.






