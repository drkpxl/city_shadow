const passport = require('passport');
const GitHubStrategy = require('passport-github2').Strategy;
const database = require('../lib/database');

function initializeAuth(app) {
  passport.use(new GitHubStrategy({
    clientID: process.env.GITHUB_CLIENT_ID,
    clientSecret: process.env.GITHUB_CLIENT_SECRET,
    callbackURL: process.env.GITHUB_CALLBACK_URL
  },
  async (accessToken, refreshToken, profile, done) => {
    try {
      // Check if user exists in database
      let user = await database.findUserByGithubId(profile.id);
      
      if (!user) {
        // Create new user
        user = await database.createUser({
          github_id: profile.id,
          username: profile.username,
          display_name: profile.displayName,
          email: profile.emails?.[0]?.value,
          avatar_url: profile.photos?.[0]?.value
        });
      } else {
        // Update last login
        await database.updateUserLogin(user.id);
      }
      
      // Check if user is enabled
      if (!user.is_enabled) {
        return done(null, false, { message: 'Your account has been disabled. Please contact an administrator.' });
      }
      
      // Add GitHub profile data to user object
      user.githubProfile = profile._json;
      
      return done(null, user);
    } catch (error) {
      console.error('Authentication error:', error);
      return done(error);
    }
  }));

  passport.serializeUser((user, done) => {
    done(null, { id: user.id, github_id: user.github_id });
  });

  passport.deserializeUser(async (serialized, done) => {
    try {
      const user = await database.findUserByGithubId(serialized.github_id);
      done(null, user);
    } catch (error) {
      done(error);
    }
  });
}

function ensureAuthenticated(req, res, next) {
  if (req.isAuthenticated()) {
    // Check if user is enabled
    if (!req.user.is_enabled) {
      req.logout((err) => {
        if (err) return next(err);
        res.status(403).send('Your account has been disabled. Please contact an administrator.');
      });
      return;
    }
    return next();
  }
  res.redirect('/login');
}

function ensureNotAuthenticated(req, res, next) {
  if (!req.isAuthenticated()) {
    return next();
  }
  res.redirect('/');
}

function ensureAdmin(req, res, next) {
  if (req.isAuthenticated() && req.user.is_admin) {
    return next();
  }
  res.status(403).send('Access denied. Admin privileges required.');
}

module.exports = {
  initializeAuth,
  ensureAuthenticated,
  ensureNotAuthenticated,
  ensureAdmin
};