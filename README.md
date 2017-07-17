# MMT-Slack-Bot

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
- [Inspiration](#inspiration)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [Challenges We Ran Into](#challenges-we-ran-into)
- [Accomplishments That We're Proud Of](#accomplishments-that-were-proud-of)
- [What We Learned](#what-we-learned)
- [What's Next for MyMusicMate](#whats-next-for-mymusicmate)
- [Commands](#commands)
- [TODOs](#todos)


## [Introduction](#introduction)
MyMusicMate is a friendly chatbot that helps you and your friends find a concert to go together based on your collective music tastes!

It's built with: [Amazon Lex](https://aws.amazon.com/lex/), [DynamoDB](https://aws.amazon.com/dynamodb/), [SNS](https://aws.amazon.com/sns/), and [Lambda](https://aws.amazon.com/lambda/) with the [Serverless Framework](https://serverless.com/) handling the deployment; [BandsInTown](http://rss.bandsintown.com/api/overview), [LastFM](http://www.last.fm/api), and [YouTube](https://developers.google.com/youtube/v3/) APIs for retrieval of concerts, artist information, and concert videos, respectively; and finally [Slack](https://slack.com/), for putting the *chat* in *chatbot*.


## [Installation](#installation)
Before deployment, you will need to provide some information for MyMusicMate to function properly.  Please open the `serverless.yml` configuration file and enter the following information
- `custom: aws: id` - Amazon AWS account number
- `environment : SLACK_APP_ID` - Slack App Client ID
- `environment : SLACK_APP_SECRET` -  Slack App Client Secret
- `environment : SLACK_APP_TOKEN` -  Slack App VerificationToken 
- `environment : LASTFM_KEY` - LastFM API key.  To obtain, create an API account and request key as per the instructions [here](http://www.last.fm/api).
- `environment : DEVELOPER_KEY` - Google/YouTube API key. To obtain, sign into the Google Developers Console and create an API key as per the instructions [here](https://developers.google.com/youtube/registering_an_application#Create_API_Keys).


## [Inspiration](#inspiration)
*"So, guys, we know we all want to go to a concert somewhere, but there are just so many options to choose from!"*

*"Yeah, and it's especially difficult because we have such varying tastes."*

*"If only there were some sort of chatbot that could take our musical preferences and somehow convert them into concert options for us…"*

*"Wouldn't that be great? And imagine if the power of Amazon Lex was used to control its conversation logic!"*

Does this conversation sound familiar to you? Well it should now, because you just read it a moment ago. Our concert-loving group of developers wanted to create a chatbot that would not only give users concert recommendations based on their music interests, whether they be by artist or by genre, but would also help them decide as a group which concert to go to. We'll even throw in some live concert videos from YouTube to help them decide!


## [What It Does](#what-it-does)
MyMusicMate starts by rounding up your concert-loving friends into a Slack channel and asking about everyone's music tastes.  Folks can name artists they like, or they can simply name genres if they don't have any specific artists in mind. MyMusicMate leverages the LastFM API to help get artist recommendations based off of user input, and then asks users to specify where they're interested in going to a concert.  For now, MyMusicMate only focuses on cities within the US, but it's learning more with every passing day/commit ;)

MyMusicMate then takes this information and uses the BandsInTown Concert Search API to find upcoming events and the YouTube Search API to find live concert videos to help users make their decision.  If you're unsure about whether or not you'd like to see an artist in person, maybe a video of a live concert could help!

Finally, MyMusicMate takes the list of concert results and concert videos and displays them in the Slack channel, allowing users to mull their decision over and place a vote for which concert the group should go to.  And don't worry - if your group can't agree on a concert, MyMusicMate will be happy to offer new suggestions or get new musical preferences until it can find what's right for you!


## [How We Built It](#how-we-built-it)
At its core, MyMusicMate is a Slack chatbot powered by Amazon Lex for its conversation logic. Lex intents are used to guide the user into inviting friends into a new Slack channel, gather everyone's musical tastes, and enter a location so MyMusicMate can start searching for concerts.  After the initial intent is triggered by a sample utterance, flow from intent to intent is handled by Amazon Lambda functions until concert voting is ready to begin. Once voting is complete, the application will either terminate if a success condition is met, or trigger a previous intent to gather more information from users.

Our Lambda functions also use Amazon's Simple Notification Service to queue actions, post messages to Slack, and communicate with Lex without fear of any function timeouts.  Lambda functions are also used for Slack integration, aiding in app installation, event subscription, and handling of interactive messages (voting) routed through Amazon API Gateway endpoints.

DynamoDB tables are used to store data that must persist through the application flow (artists, genres, concerts, etc.) and beyond (user IDs, team IDs, access tokens, etc.). Artists and genres are discarded when users have exhausted their concert options and decide to expand their search preferences, while concerts are kept until the application terminates, in order to ensure duplicate recommendations are not delivered. State (current intent, channel id, timeout) and current intent data (callback_IDs, user input) are also stored, allowing multiple users to converse with Lex freely without fear of accidentally invoking other intents.

MyMusicMate leverages multiple APIs to validate user input and find events for users. The LastFM Album Search API is used to get related artists by genre, while the BandsInTown Artist and Concert Search APIs are used to verify artist names, US city names, and search for concerts by specified and related artists.  Finally, the YouTube Search API is used to search for live concert videos, after which all of the content is rolled up and passed to the Slack messaging API in neatly formatted messages.

Our team used the Serverless Framework to build and deploy our application onto the AWS stack.  One of our developers also created a plug-in for the Serverless framework to deploy our Lex bot from a blueprint file, which is hopefully available as a npm package by the time you read this :)


## [Challenges We Ran Into](#challenges-we-ran-into)
Our team ran into a number of challenges during development. Being a newly available technology, references were sparse so we were not able to find the exact behavior of some of Amazon Lex slot types, which led to some guesses on how user input would be interpreted. 

Creating a Lex intent loop was also a bit harder than expected, and we wound up using a continuous ConfirmIntent loop with multiple optional Slot Types as a bit of a hack.  As a result, we had to perform additional user input validation to ensure Lex wasn't registering a "negative" sounding artist name as a "status denied" confirmation, as was the case for the DJ name "What So Not" for example. 

Creating a proper timer also proved to be an issue, as we wanted to give the user an option to extend the timer while being mindful of Lex timeouts.  We eventually decided on storing the time with the rest of the "state" information, which allowed us to restore state without worry of intent expiration.

Prioritizing concerts was also a hurdle, as we had to factor in the nature of the search result (whether it was by related artist, by genre, etc.), whether or not there was any artist overlap with previously displayed events, and whether or not the event received a certain percentage of votes in a previous round of voting.
If you plan on terminating a voting process after the last vote is placed, leave a bit of a buffer for misclicks and changed opinions. People love to change their mind after a vote has been placed.


## [Accomplishments That We're Proud Of](#accomplishments-that-were-proud-of)
First and foremost, we are proud of putting together an application that leverages a number of technologies that we had never used before (Lex, DynamoDB, Slack API, Lambda) in a short period of time.  We've grown as developers, and some would say, as people. \**cue awws from the audience*\*

We were also proud of how we implemented state management with DynamoDB, storing interim event data to allow us to reliably poll users for input inside or outside of intents without accidentally invoking another intent or triggering a Lambda function.  Once we were able to control state flow, we didn't have to worry about how making our Lex interactions less "bot-like" might affect MyMusicMate's behavior.

We're also pretty happy with our concert queue/voting logic.  Ultimately we wanted to give users the highest chance of coming to an agreement on which concert to go to, and this meant giving enough of a variety of concerts, setting the proper threshold for keeping or discarding events, and allowing just enough rounds of voting necessary to make a refined decision without getting stuck in a voting loop.

## [What We Learned](#what-we-learned)
**Double-verify user input.** Even if you using a pre-existing Amazon Slot type, stick a Lambda verification function behind it.

**Print long, print strong.** If you're going to be manually controlling Lex intent flow, you'll be looking at event contents constantly.  Like, never comment out a print event statement. Ever.

**Be human.** Writing multiple, informal intent utterances and response messages can go a long way in making bot interactions seem more "human," while repeated responses or responses in ALL CAPS can result in a colder, more jarring experience for the user.

**People make mistakes.** If you plan on terminating a voting process after the last vote is placed, leave a bit of a buffer for misclicks and changed opinions. People love to change their mind after a vote has been placed.

## [What's Next for MyMusicMate](#whats-next-for-mymusicmate)
**Expand concert search.**  We'd like to accomplish this in two ways: First, we want to leverage other event search APIs, such as Songkick and Eventful, so MyMusicMate would have a greater library of concerts to parse through.  Second, we'd like to expand support for cities outside of the US, starting with the rest of North America.

**Fuzzy search and related genres.**  We'd like to implement fuzzy searching to allow for more accurate resolution of misspelled genres and artist names, as well as a "related genre" search to be used when the current search scheme does not return a sufficient number of events.

**Headless browser to unfurl redirected content.**  Our current ticket links contain a JavaScript redirect to each event's respective ticketing page.  We will use a headless browser to grab the redirect link so metadata can be unfurled inside the final Slack message.

**Amazon Polly Integration.** . We originally planned on integrating Polly with MyMusicMate, to allow for seamless concert recommendations based on users talking to each other about their musical preferences.  Unfortunately we didn't have enough time to accomplish this, but we would love to revisit this idea in the future.

**Smarter YouTube searches.**  We'd like to redefine our YouTube search to prioritize videos from Artists' official Vevo pages and use the YouTube Music Insights API to prioritize videos based on popularity by location, depending on the user's city.


## [Commands](#commands)
- `sls deploy` - deploy lambda functions, API gateways, DynamoDB tables to AWS
- `sls lex` - deploy a lex bot to AWS

## [TODOs](#todos)
- Create a lex with boto3 lex-model api
- Create a flow to move between lex intents

