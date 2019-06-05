'use strict';

var bless             =   require('gulp-bless'),
    gulp              =   require('gulp'),
    sass              =   require('gulp-sass'),
    sassLint          =   require('gulp-sass-lint'),
    sassGlob          =   require('gulp-sass-glob'),
    cleanCSSMinify    =   require('gulp-clean-css'),
    gzip              =   require('gulp-gzip'),
    notify            =   require('gulp-notify'),
    rename            =   require("gulp-rename"),
    sourcemaps        =   require('gulp-sourcemaps'),
    minify            =   require('gulp-minify');

  gulp.task('styles', function() {
    return gulp.src('cspatients/static/styles/main.s+(a|c)ss')
      .pipe(sourcemaps.init())
        .pipe(sassGlob())
        .pipe(sass().on('error', sass.logError))
        .pipe(bless())
        .pipe(cleanCSSMinify())
      .pipe(sourcemaps.write('/maps'))
      .pipe(gulp.dest('cspatients/static/'))
      .pipe(rename({ suffix: ".min" }))
      .pipe(notify({ message: `Styles task complete: Done`}));
  });
  gulp.task('default', ['styles']);
